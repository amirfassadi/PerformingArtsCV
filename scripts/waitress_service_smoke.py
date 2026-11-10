import http.client
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE_FILE = ROOT / 'deploy' / 'performingartscv.service.example'


def service_command(port, application):
    line = next(
        line.split('=', 1)[1].strip()
        for line in SERVICE_FILE.read_text(encoding='utf-8').splitlines()
        if line.startswith('ExecStart=')
    )
    tokens = shlex.split(line, posix=True)
    tokens[0] = sys.executable
    tokens[-1] = application
    for index, token in enumerate(tokens):
        if token.startswith('--listen='):
            tokens[index] = f'--listen=127.0.0.1:{port}'
    parsed_headers = next(
        token.split('=', 1)[1] for token in tokens
        if token.startswith('--trusted-proxy-headers=')
    )
    assert set(parsed_headers.split()) == {'x-forwarded-for', 'x-forwarded-proto'}
    assert tokens.count('--trusted-proxy-headers=x-forwarded-for x-forwarded-proto') == 1
    return tokens


def wait_for_port(port):
    for _ in range(100):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError('Waitress did not start')


def request(port, path, forwarded):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    connection.request(
        'GET',
        path,
        headers={'X-Forwarded-For': forwarded, 'X-Forwarded-Proto': 'https'},
    )
    response = connection.getresponse()
    body = json.loads(response.read())
    connection.close()
    return response.status, body


def fixture_smoke(work):
    fixture = work / 'fixture.py'
    fixture.write_text(
        "import json\n"
        "def application(environ, start_response):\n"
        "    body = json.dumps({'identity': environ.get('REMOTE_ADDR'),"
        " 'scheme': environ.get('wsgi.url_scheme')}).encode()\n"
        "    start_response('200 OK', [('Content-Type', 'application/json'),"
        " ('Content-Length', str(len(body)))])\n"
        "    return [body]\n",
        encoding='utf-8',
    )
    port = 61201
    process = subprocess.Popen(
        service_command(port, 'fixture:application'),
        cwd=work,
        env=os.environ | {'PYTHONPATH': str(work)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for_port(port)
        first = request(port, '/', '198.51.100.10')
        second = request(port, '/', '203.0.113.20')
        forged = request(port, '/', '198.51.100.10, 203.0.113.20')
        assert first[1] == {'identity': '198.51.100.10', 'scheme': 'https'}
        assert second[1] == {'identity': '203.0.113.20', 'scheme': 'https'}
        assert forged[1]['identity'] == '203.0.113.20'
    finally:
        process.terminate()
        process.wait(timeout=10)


def django_smoke(work):
    environment = os.environ | {
        'DATA_ROOT': str(work / 'data'),
        'PRIVATE_MEDIA_ROOT': str(work / 'private-media'),
        'DJANGO_DEBUG': '1',
        'DJANGO_SECRET_KEY': 'service-smoke-only',
        'DJANGO_ALLOWED_HOSTS': '127.0.0.1,localhost',
        'CSRF_TRUSTED_ORIGINS': 'https://127.0.0.1:61202',
        'LOGIN_RATE_LIMIT': '2',
        'LOGIN_RATE_WINDOW': '3600',
    }
    (work / 'data').mkdir()
    subprocess.run(
        [sys.executable, 'manage.py', 'migrate', '--noinput'],
        cwd=ROOT, env=environment, check=True,
        stdout=subprocess.DEVNULL,
    )
    port = 61202
    process = subprocess.Popen(
        service_command(port, 'config.wsgi:application'),
        cwd=ROOT, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    try:
        wait_for_port(port)
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        connection.request('GET', '/login/')
        response = connection.getresponse()
        page = response.read().decode()
        cookie = response.getheader('Set-Cookie').split(';', 1)[0]
        token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"', page,
        ).group(1)
        connection.close()
        statuses = []
        for path in ('/login/', '/admin/login/', '/login/'):
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request(
                'POST', path,
                body=urllib.parse.urlencode({
                    'csrfmiddlewaretoken': token,
                }),
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Cookie': cookie,
                    'Origin': 'https://127.0.0.1:61202',
                    'X-Forwarded-For': '198.51.100.10',
                    'X-Forwarded-Proto': 'https',
                },
            )
            response = connection.getresponse()
            response.read()
            statuses.append(response.status)
            connection.close()
        assert statuses == [200, 200, 429], statuses
    finally:
        process.terminate()
        process.wait(timeout=10)


def main():
    with tempfile.TemporaryDirectory(prefix='performingartscv-service-smoke-') as folder:
        work = Path(folder)
        fixture_smoke(work)
        django_smoke(work)
    print('PASS: service ExecStart parsing, trusted identities, HTTPS, spoof handling, and Django login/admin shared quota')


if __name__ == '__main__':
    main()
