import http.client
import json
import socket
import threading
from collections import Counter

from waitress import serve
from waitress.proxy_headers import proxy_headers_middleware


LIMIT = 2


def application(environ, start_response):
    identity = environ.get('REMOTE_ADDR') or 'unknown'
    application.attempts[identity] += 1
    status = '200 OK' if application.attempts[identity] <= LIMIT else '429 Too Many Requests'
    payload = json.dumps({
        'identity': identity,
        'attempt': application.attempts[identity],
        'path': environ.get('PATH_INFO'),
    }).encode()
    start_response(status, [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(payload))),
    ])
    return [payload]


application.attempts = Counter()


def request(port, path, forwarded=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    headers = {}
    if forwarded is not None:
        headers['X-Forwarded-For'] = forwarded
    connection.request('GET', path, headers=headers)
    response = connection.getresponse()
    body = json.loads(response.read())
    connection.close()
    return response.status, body


def assert_untrusted_peer_is_cleared():
    seen = {}

    def app(environ, start_response):
        seen.update(environ)
        start_response('200 OK', [('Content-Length', '0')])
        return [b'']

    wrapped = proxy_headers_middleware(
        app,
        trusted_proxy='127.0.0.1',
        trusted_proxy_count=1,
        trusted_proxy_headers={'x-forwarded-for', 'x-forwarded-proto'},
        clear_untrusted=True,
    )
    wrapped({
        'REMOTE_ADDR': '192.0.2.44',
        'HTTP_X_FORWARDED_FOR': '198.51.100.10',
        'HTTP_X_FORWARDED_PROTO': 'https',
    }, lambda status, headers: None)
    assert 'HTTP_X_FORWARDED_FOR' not in seen
    assert 'HTTP_X_FORWARDED_PROTO' not in seen


def main():
    assert_untrusted_peer_is_cleared()
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    thread = threading.Thread(
        target=serve,
        kwargs={
            'app': application,
            'host': '127.0.0.1',
            'port': port,
            'trusted_proxy': '127.0.0.1',
            'trusted_proxy_count': 1,
            'trusted_proxy_headers': {'x-forwarded-for', 'x-forwarded-proto'},
            'clear_untrusted_proxy_headers': True,
            'threads': 4,
        },
        daemon=True,
    )
    thread.start()
    for _ in range(50):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                break
        except OSError:
            continue
    else:
        raise RuntimeError('Waitress did not start')
    first = request(port, '/login/', '198.51.100.10')
    second = request(port, '/admin/login/', '198.51.100.10')
    blocked = request(port, '/login/', '198.51.100.10')
    other = request(port, '/login/', '203.0.113.20')
    other_admin = request(port, '/admin/login/', '203.0.113.20')
    chain = request(port, '/login/', '198.51.100.10, 203.0.113.20')
    chain_blocked = request(port, '/login/', '198.51.100.10, 203.0.113.20')
    assert first[1]['identity'] == '198.51.100.10'
    assert second[1]['identity'] == '198.51.100.10'
    assert first[0] == second[0] == 200
    assert blocked[0] == 429
    assert other[0] == other_admin[0] == 200
    assert other[1]['identity'] == other_admin[1]['identity'] == '203.0.113.20'
    assert chain[0] == 429 and chain[1]['identity'] == '203.0.113.20'
    assert chain_blocked[0] == 429
    print('PASS: real Waitress trusted peer, distinct identities, shared login/admin quota, and anti-spoof checks')


if __name__ == '__main__':
    main()
