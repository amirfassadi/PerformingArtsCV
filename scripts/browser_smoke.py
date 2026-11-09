"""Exercise real browser -> Django -> disk, then restore an isolated snapshot."""
import argparse
import base64
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')

def run_manage(environment, *args):
    result = subprocess.run([sys.executable, 'manage.py', *args], cwd=ROOT, env=environment,
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--screenshots', type=Path)
    options = parser.parse_args()
    screenshots = options.screenshots.resolve() if options.screenshots else None
    if screenshots:
        screenshots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='performingartscv-qa-') as temporary:
        work = Path(temporary).resolve()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        environment = os.environ | {
            'DATA_ROOT': str(work / 'original'),
            'PRIVATE_MEDIA_ROOT': str(work / 'original' / 'private-media'),
            'DJANGO_DEBUG': '1', 'DJANGO_ALLOWED_HOSTS': '127.0.0.1,localhost',
            'PUBLIC_BASE_URL': base, 'DJANGO_SECRET_KEY': secrets.token_urlsafe(48),
            'ZARINPAL_MERCHANT_ID': '', 'ZARINPAL_SANDBOX': '1',
            'TRUST_PROXY_HTTPS': '0', 'PYTHONIOENCODING': 'utf-8',
        }
        run_manage(environment, 'migrate', '--noinput')
        server_log = (work / 'server.log').open('w', encoding='utf-8')
        server = subprocess.Popen(
            [sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload'],
            cwd=ROOT, env=environment, stdout=server_log, stderr=server_log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        try:
            local_http = build_opener(ProxyHandler({}))
            for _ in range(80):
                try:
                    with local_http.open(base, timeout=1) as response:
                        if response.status == 200:
                            break
                except (URLError, OSError):
                    time.sleep(0.15)
            else:
                server_log.flush()
                raise RuntimeError('Local QA server did not start:\n' + (work / 'server.log').read_text(encoding='utf-8'))
            errors = []
            with sync_playwright() as playwright:
                edge = Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
                browser = playwright.chromium.launch(headless=True, **({'executable_path': str(edge)} if edge.is_file() else {}))
                context = browser.new_context(viewport={'width': 1440, 'height': 1050}, locale='fa-IR')
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('response', lambda response: errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 500 else None)
                page.goto(base)
                if screenshots:
                    page.screenshot(path=str(screenshots / 'home-desktop.png'), full_page=True)

                def signup(username):
                    page.goto(base + '/signup/')
                    page.locator('#id_username').fill(username)
                    page.locator('#id_email').fill(username + '@example.test')
                    password = secrets.token_urlsafe(24)
                    page.locator('#id_password1').fill(password)
                    page.locator('#id_password2').fill(password)
                    page.get_by_role('button', name='ثبت‌نام و ساخت صفحه').click()
                    expect(page).to_have_url(base + '/dashboard/')

                signup('qa_artist')
                page.goto(base + '/dashboard/edit/')
                page.locator('#id_display_name').fill('بازیگر آزمایشی')
                page.locator('#id_city').fill('تهران')
                page.locator('#id_specialty').fill('بازیگر تئاتر')
                page.locator('#id_skills').fill('بداهه‌پردازی، بیان و حرکت')
                page.locator('#id_biography').fill('این رزومه فقط برای بررسی عملکرد نسخه اولیه ساخته شده است.')
                page.locator('#id_published').check()
                page.get_by_role('button', name='ذخیره', exact=True).click()
                page.goto(base + '/dashboard/upload/')
                page.locator('#id_title').fill('نمونه‌کار آزمایشی')
                page.locator('#id_file').set_input_files({'name': 'sample.png', 'mimeType': 'image/png', 'buffer': PNG})
                page.get_by_role('button', name='ذخیره', exact=True).click()
                expect(page.get_by_role('heading', name='نمونه‌کار آزمایشی')).to_be_visible()
                image = page.locator('.media-card img')
                expect(image).to_be_visible()
                if not image.evaluate('(image) => image.complete && image.naturalWidth > 0'):
                    raise AssertionError('Uploaded image did not decode in the browser')
                file_path = image.get_attribute('src')
                profile_path = page.get_by_role('link', name='پیش‌نمایش رزومه').get_attribute('href')
                if screenshots:
                    page.screenshot(path=str(screenshots / 'dashboard-desktop.png'), full_page=True)
                page.get_by_role('button', name='خروج', exact=True).click()
                signup('qa_viewer')
                assert page.goto(base + '/artists/').status == 403
                assert page.request.get(base + file_path).status == 403
                expect(page.get_by_role('heading', name='برای کشف استعدادها، اشتراک مشاهده لازم است.')).to_be_visible()
                run_manage(environment, 'shell', '-c',
                    "from django.contrib.auth.models import User; from portfolio.models import Entitlement; "
                    "from django.utils import timezone; from datetime import timedelta; "
                    "Entitlement.objects.create(user=User.objects.get(username='qa_viewer'),kind='browse',"
                    "ends_at=timezone.now()+timedelta(days=1),reference='isolated-browser-qa')")
                assert page.goto(base + '/artists/?q=بازیگر').status == 200
                page.get_by_role('link').filter(has_text='بازیگر آزمایشی').click()
                expect(page.get_by_role('heading', name='بازیگر آزمایشی', exact=True)).to_be_visible()
                assert page.request.get(base + file_path).status == 200
                page.get_by_role('button', name='+ افزودن به منتخب‌ها').click()
                expect(page.get_by_role('button', name='حذف از منتخب‌ها')).to_be_visible()
                page.set_viewport_size({'width': 390, 'height': 844})
                page.goto(base + '/artists/')
                expect(page.get_by_role('heading', name='بازیگر آزمایشی', exact=True)).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                if screenshots:
                    page.screenshot(path=str(screenshots / 'directory-mobile.png'), full_page=True)
                page.goto(base + profile_path)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                if errors:
                    raise AssertionError('\n'.join(errors))
                context.close()
                browser.close()
            run_manage(environment, 'backup_site', str(work / 'snapshot'))
            run_manage(environment, 'verify_backup', str(work / 'snapshot'))
            restored = work / 'restored'
            restored.mkdir()
            shutil.copyfile(work / 'snapshot' / 'db.sqlite3', restored / 'db.sqlite3')
            shutil.copytree(work / 'snapshot' / 'private-media', restored / 'private-media')
            restore_env = environment | {'DATA_ROOT': str(restored), 'PRIVATE_MEDIA_ROOT': str(restored / 'private-media')}
            run_manage(restore_env, 'check')
            run_manage(restore_env, 'shell', '-c',
                "from portfolio.models import Profile,PortfolioFile; "
                "assert Profile.objects.count()==2; f=PortfolioFile.objects.get(); "
                "assert f.file.open('rb').read(8)==b'\\x89PNG\\r\\n\\x1a\\n'")
            print('PASS: browser signup, profile edit, private upload, paywall, paid browsing, favorites, mobile, backup and restored data.')
        finally:
            server.terminate()
            server.wait(timeout=15)
            server_log.close()

if __name__ == '__main__':
    main()
