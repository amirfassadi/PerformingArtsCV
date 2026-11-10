"""Exercise real browser -> Django -> disk, then restore an isolated snapshot."""
import argparse
import base64
from contextlib import contextmanager
import os
import re
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
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg==')

def run_manage(environment, *args):
    result = subprocess.run([sys.executable, 'manage.py', *args], cwd=ROOT, env=environment,
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


@contextmanager
def temporary_workspace():
    temporary = tempfile.TemporaryDirectory(prefix='performingartscv-qa-')
    primary_error = None
    try:
        yield Path(temporary.name).resolve()
    except BaseException as error:
        primary_error = error
        raise
    finally:
        failures = cleanup_steps([('temporary workspace', lambda: cleanup_temporary_workspace(temporary))])
        report_cleanup_failures(failures, primary_error)


def cleanup_temporary_workspace(temporary):
    for attempt in range(10):
        try:
            temporary.cleanup()
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.2)


def cleanup_steps(steps):
    failures = []
    for label, cleanup in steps:
        try:
            cleanup()
        except Exception as error:
            failures.append(f'{label}: {type(error).__name__}: {error}')
    return failures


def report_cleanup_failures(failures, primary_error):
    if not failures:
        return
    message = 'Cleanup failed:\n' + '\n'.join(f'- {failure}' for failure in failures)
    if primary_error is not None:
        print(message, file=sys.stderr)
    else:
        raise RuntimeError(message)


def stop_server(server):
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=15)
    if server.poll() is None:
        raise RuntimeError('Local QA server is still running after terminate/kill.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--screenshots', type=Path)
    options = parser.parse_args()
    screenshots = options.screenshots.resolve() if options.screenshots else None
    if screenshots:
        screenshots.mkdir(parents=True, exist_ok=True)
    with temporary_workspace() as work:
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
        inviter_token = run_manage(
            environment, 'shell', '-c',
            "from django.contrib.auth.models import User; from portfolio.models import Profile; "
            "inviter=User.objects.create_user(username='qa_inviter',password='Synthetic-inviter-password-1'); "
            "Profile.objects.create(user=inviter,display_name='دعوت‌کننده اولیه'); "
            "print(inviter.invitation_link.token)",
        ).strip().splitlines()[-1]
        server_log = None
        server = None
        try:
            server_log = (work / 'server.log').open('w', encoding='utf-8')
            server = subprocess.Popen(
                [sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload'],
                cwd=ROOT, env=environment, stdout=server_log, stderr=server_log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
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
                context = None
                try:
                    context = browser.new_context(
                        viewport={'width': 1440, 'height': 1050},
                        locale='fa-IR',
                        permissions=['clipboard-read', 'clipboard-write'],
                    )
                    page = context.new_page()
                    signup_posts = []
                    page.on(
                        'request',
                        lambda request: signup_posts.append(request.headers)
                        if request.method == 'POST' and '/signup/' in request.url else None,
                    )
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.on('response', lambda response: errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 500 else None)
                    page.goto(base)
                    video_base64 = page.evaluate("""async () => {
                        const canvas = document.createElement('canvas');
                        canvas.width = 160;
                        canvas.height = 90;
                        const context = canvas.getContext('2d');
                        const mimeType = 'video/mp4;codecs=avc1.42E01E';
                        if (!MediaRecorder.isTypeSupported(mimeType)) {
                            throw new Error('Edge does not support H.264 MP4 recording.');
                        }
                        const draw = frame => {
                            context.fillStyle = `hsl(${frame * 25 % 360} 80% 45%)`;
                            context.fillRect(0, 0, canvas.width, canvas.height);
                            context.fillStyle = 'white';
                            context.font = '20px sans-serif';
                            context.fillText('Synthetic video ' + frame, 12, 48);
                        };
                        draw(0);
                        const stream = canvas.captureStream(12);
                        const recorder = new MediaRecorder(stream, {mimeType});
                        const chunks = [];
                        recorder.ondataavailable = event => {
                            if (event.data.size) chunks.push(event.data);
                        };
                        const stopped = new Promise((resolve, reject) => {
                            recorder.onstop = resolve;
                            recorder.onerror = event => reject(event.error);
                        });
                        recorder.start();
                        let frame = 0;
                        const timer = setInterval(() => draw(++frame), 100);
                        await new Promise(resolve => setTimeout(resolve, 1800));
                        recorder.stop();
                        await stopped;
                        stream.getTracks().forEach(track => track.stop());
                        clearInterval(timer);
                        const blob = new Blob(chunks, {type: recorder.mimeType});
                        if (blob.size < 100) throw new Error(`Recorded video is unexpectedly small: ${blob.size}`);
                        const bytes = new Uint8Array(await blob.arrayBuffer());
                        let binary = '';
                        for (let offset = 0; offset < bytes.length; offset += 0x8000) {
                            binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
                        }
                        return btoa(binary);
                    }""")
                    video_payload = base64.b64decode(video_base64)
                    if screenshots:
                        page.screenshot(path=str(screenshots / 'home-desktop.png'), full_page=True)

                    def signup(username, invitation_url):
                        page.goto(invitation_url)
                        page.locator('#id_username').fill(username)
                        page.locator('#id_email').fill(username + '@example.test')
                        password = secrets.token_urlsafe(24)
                        page.locator('#id_password1').fill(password)
                        page.locator('#id_password2').fill(password)
                        page.get_by_role('button', name='ثبت‌نام و ساخت صفحه').click()
                        expect(page).to_have_url(base + '/dashboard/')
                        origin = signup_posts[-1].get('origin')
                        referer = signup_posts[-1].get('referer', '')
                        if origin != base or referer.rstrip('/') != base:
                            raise AssertionError(f'Unexpected invitation signup origin/referrer: {origin!r}, {referer!r}')
                        if invitation_url.rstrip('/').rsplit('/', 1)[-1] in referer:
                            raise AssertionError('Invitation token leaked in the signup request referrer.')
                        return password

                    def login(username, password):
                        page.goto(base + '/login/')
                        page.locator('#id_username').fill(username)
                        page.locator('#id_password').fill(password)
                        page.get_by_role('button', name='ورود').click()
                        expect(page).to_have_url(base + '/dashboard/')

                    def logout():
                        page.get_by_role('button', name='خروج', exact=True).click()

                    artist_password = signup('qa_artist', f'{base}/signup/{inviter_token}/')
                    page.goto(base + '/dashboard/')
                    invitation_input = page.locator('#invitation-url')
                    artist_invitation_url = invitation_input.input_value()
                    if not artist_invitation_url.startswith(base + '/signup/'):
                        raise AssertionError('Dashboard did not expose a valid invitation signup URL.')
                    page.get_by_role('button', name='کپی لینک').click()
                    copy_status = page.locator('#invitation-copy-status')
                    expect(copy_status).to_have_text(
                        re.compile(r'^(لینک دعوت کپی شد\.|لینک انتخاب شد؛ آن را کپی کن\.)$'),
                    )
                    if copy_status.inner_text() == 'لینک دعوت کپی شد.':
                        if page.evaluate('navigator.clipboard.readText()') != artist_invitation_url:
                            raise AssertionError('Clipboard content did not match the displayed invitation URL.')
                        copy_result = 'clipboard'
                    elif copy_status.inner_text() == 'لینک انتخاب شد؛ آن را کپی کن.':
                        selection = invitation_input.evaluate(
                            '(input) => input.selectionStart === 0 && input.selectionEnd === input.value.length',
                        )
                        if not selection:
                            raise AssertionError('Clipboard fallback did not select the invitation URL.')
                        copy_result = 'fallback selection'
                    else:
                        raise AssertionError(f'Unexpected copy result: {copy_status.inner_text()!r}')

                    profile_path = page.get_by_role('link', name='پیش‌نمایش رزومه').get_attribute('href')
                    page.goto(base + profile_path)
                    expect(page.get_by_text('این رزومه پیش‌نویس است؛ فقط خودت می‌توانی آن را ببینی.')).to_be_visible()
                    expect(page.get_by_role('heading', name='بازیگر آزمایشی')).to_have_count(0)

                    page.goto(base + '/dashboard/edit/')
                    page.locator('#id_display_name').fill('بازیگر آزمایشی')
                    page.locator('#id_city').fill('تهران')
                    page.locator('#id_specialty').fill('بازیگر تئاتر')
                    page.locator('#id_skills').fill('بداهه‌پردازی، بیان و حرکت')
                    page.locator('#id_biography').fill(
                        "<script>document.body.dataset.synthetic='executed'</script>",
                    )
                    page.locator('#id_experience').fill('اجرای آزمایشی')
                    page.locator('#id_contact').fill('public-studio@example.test')
                    page.locator('#id_published').check()
                    page.get_by_role('button', name='ذخیره', exact=True).click()
                    expect(page.locator('body')).to_contain_text('قابل مشاهده برای مشترکان')
                    page.goto(base + profile_path)
                    expect(page.get_by_role('heading', name='بازیگر آزمایشی', exact=True)).to_be_visible()
                    expect(page.locator('.prose').first).to_contain_text(
                        "<script>document.body.dataset.synthetic='executed'</script>",
                    )
                    if page.locator('script').count() or page.evaluate(
                        "document.body.dataset.synthetic === 'executed'",
                    ):
                        raise AssertionError('Profile text was executed as HTML/script.')
                    if 'qa_artist@example.test' in page.locator('body').inner_text():
                        raise AssertionError('Private account email appeared on the profile.')
                    expect(page.locator('body')).to_contain_text('public-studio@example.test')

                    def verify_canvas_image(title, suffix, mime_type):
                        encoded_image = page.evaluate("""async ({mimeType, label}) => {
                            const canvas = document.createElement('canvas');
                            canvas.width = 160;
                            canvas.height = 90;
                            const context = canvas.getContext('2d');
                            context.fillStyle = '#336699';
                            context.fillRect(0, 0, canvas.width, canvas.height);
                            context.fillStyle = 'white';
                            context.fillText(label, 8, 45);
                            const blob = await new Promise(resolve => canvas.toBlob(resolve, mimeType));
                            if (!blob) throw new Error(`${mimeType} encoding is unavailable.`);
                            const bytes = new Uint8Array(await blob.arrayBuffer());
                            let binary = '';
                            for (let offset = 0; offset < bytes.length; offset += 0x8000) {
                                binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
                            }
                            return btoa(binary);
                        }""", {'mimeType': mime_type, 'label': title})
                        page.goto(base + '/dashboard/upload/')
                        page.locator('#id_title').fill(title)
                        page.locator('#id_file').set_input_files({
                            'name': f'sample.{suffix}',
                            'mimeType': mime_type,
                            'buffer': base64.b64decode(encoded_image),
                        })
                        page.get_by_role('button', name='ذخیره', exact=True).click()
                        card = page.locator('.media-card').filter(has_text=title)
                        expect(card).to_be_visible()
                        image = card.locator('img')
                        if not image.evaluate(
                            '(image) => image.complete && image.naturalWidth === 160 && image.naturalHeight === 90',
                        ):
                            raise AssertionError(f'Uploaded {mime_type} image did not decode in the browser.')
                        card.get_by_role('button', name='حذف فایل').click()
                        expect(page.locator('.media-card').filter(has_text=title)).to_have_count(0)

                    verify_canvas_image('تصویر JPEG آزمایشی', 'jpg', 'image/jpeg')
                    verify_canvas_image('تصویر WebP آزمایشی', 'webp', 'image/webp')

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
                    expect(page.locator('.storage-panel')).to_contain_text('100 مگابایت')
                    page.goto(base + '/dashboard/upload/')
                    page.locator('#id_title').fill('ویدئوی آزمایشی')
                    page.locator('#id_file').set_input_files({
                        'name': 'sample.mp4',
                        'mimeType': 'video/mp4',
                        'buffer': video_payload,
                    })
                    page.get_by_role('button', name='ذخیره', exact=True).click()
                    expect(page.get_by_role('heading', name='ویدئوی آزمایشی')).to_be_visible()
                    video = page.locator('.media-card video')
                    expect(video).to_be_visible()
                    video_path = video.get_attribute('src')
                    video_response = page.request.get(base + video_path)
                    if video_response.status != 200 or video_response.headers.get('content-type') != 'video/mp4':
                        raise AssertionError('Uploaded video was not delivered by the private media endpoint.')
                    playback = video.evaluate("""async video => {
                        video.muted = true;
                        await new Promise((resolve, reject) => {
                            const timeout = setTimeout(() => reject(new Error('Video metadata timed out.')), 5000);
                            video.addEventListener('loadedmetadata', () => {
                                clearTimeout(timeout);
                                resolve();
                            }, {once: true});
                            video.addEventListener('error', () => reject(new Error('Video metadata could not be decoded.')), {once: true});
                            video.load();
                        });
                        await video.play();
                        await new Promise((resolve, reject) => {
                            const timeout = setTimeout(() => reject(new Error('Video frame timed out.')), 5000);
                            if (video.requestVideoFrameCallback) {
                                video.requestVideoFrameCallback(() => {
                                    clearTimeout(timeout);
                                    resolve();
                                });
                            } else {
                                video.addEventListener('timeupdate', () => {
                                    clearTimeout(timeout);
                                    resolve();
                                }, {once: true});
                            }
                        });
                        await new Promise((resolve, reject) => {
                            const deadline = Date.now() + 2000;
                            const checkProgress = () => {
                                if (video.currentTime >= 0.2) {
                                    resolve();
                                } else if (Date.now() >= deadline) {
                                    reject(new Error('Video playback did not advance.'));
                                } else {
                                    setTimeout(checkProgress, 25);
                                }
                            };
                            checkProgress();
                        });
                        const result = {
                            duration: video.duration,
                            width: video.videoWidth,
                            height: video.videoHeight,
                            currentTime: video.currentTime,
                            readyState: video.readyState,
                        };
                        video.pause();
                        return result;
                    }""")
                    if (playback['duration'] <= 0 or playback['width'] != 160
                            or playback['height'] != 90 or playback['currentTime'] < 0.2
                            or playback['readyState'] < 2):
                        raise AssertionError(f'Video did not play a decoded frame: {playback!r}')

                    page.goto(base + '/dashboard/links/add/')
                    page.locator('#id_title').fill('لینک نمونه‌کار ساختگی')
                    page.locator('#id_url').fill('https://example.test/synthetic-work')
                    page.get_by_role('button', name='ذخیره', exact=True).click()
                    page.goto(base + '/dashboard/')
                    external_link = page.locator('.link-row').filter(has_text='لینک نمونه‌کار ساختگی')
                    if external_link.locator('a').get_attribute('href') != 'https://example.test/synthetic-work':
                        raise AssertionError('The external work link did not preserve its validated URL.')
                    external_link.get_by_role('button', name='حذف').click()
                    expect(page.locator('body')).not_to_contain_text('لینک نمونه‌کار ساختگی')
                    profile_path = page.get_by_role('link', name='پیش‌نمایش رزومه').get_attribute('href')
                    if screenshots:
                        page.screenshot(path=str(screenshots / 'dashboard-desktop.png'), full_page=True)
                    logout()

                    viewer_password = signup('qa_viewer', artist_invitation_url)
                    page.goto(base + '/dashboard/edit/')
                    page.locator('#id_display_name').fill('بیننده آزمایشی')
                    page.get_by_role('button', name='ذخیره', exact=True).click()
                    logout()
                    login('qa_artist', artist_password)
                    invitation_panel = page.locator('section[aria-labelledby="invitation-heading"]')
                    expect(invitation_panel).to_contain_text('1 دعوت')
                    expect(invitation_panel).to_contain_text('بیننده آزمایشی')
                    if 'qa_viewer@example.test' in invitation_panel.inner_text():
                        raise AssertionError('Invitation dashboard exposed the invitee email address.')

                    run_manage(environment, 'shell', '-c',
                        "from portfolio.models import InvitationLink; "
                        "InvitationLink.objects.filter(user__username='qa_artist').update(is_active=False)")
                    page.reload()
                    expect(invitation_panel.get_by_text('لینک دعوت این حساب توسط مدیر غیرفعال شده است')).to_be_visible()
                    expect(invitation_panel).to_contain_text('1 دعوت')
                    expect(invitation_panel).to_contain_text('بیننده آزمایشی')
                    if page.locator('#invitation-url').count() or page.locator('#copy-invitation').count():
                        raise AssertionError('Dashboard still offered the disabled invitation link.')

                    logout()
                    login('qa_viewer', viewer_password)
                    assert page.goto(base + '/artists/').status == 403
                    assert page.request.get(base + file_path).status == 403
                    expect(page.get_by_role('heading', name='برای کشف استعدادها، اشتراک مشاهده لازم است.')).to_be_visible()
                    run_manage(environment, 'shell', '-c',
                        "from django.contrib.auth.models import User; from portfolio.models import Entitlement; "
                        "from django.utils import timezone; from datetime import timedelta; "
                        "Entitlement.objects.create(user=User.objects.get(username='qa_viewer'),kind='browse',"
                        "ends_at=timezone.now()+timedelta(days=1),reference='isolated-browser-qa')")
                    assert page.goto(base + '/artists/?q=بازیگر&city=تهران').status == 200
                    page.get_by_role('link').filter(has_text='بازیگر آزمایشی').click()
                    expect(page.get_by_role('heading', name='بازیگر آزمایشی', exact=True)).to_be_visible()
                    assert page.request.get(base + profile_path).status == 200
                    assert page.request.get(base + file_path).status == 200
                    video_response = page.request.get(base + video_path)
                    if video_response.status != 200 or video_response.headers.get('content-type') != 'video/mp4':
                        raise AssertionError('Viewer could not access the published video with an active grant.')
                    page.get_by_role('button', name='+ افزودن به منتخب‌ها').click()
                    expect(page.get_by_role('button', name='حذف از منتخب‌ها')).to_be_visible()
                    page.get_by_role('button', name='حذف از منتخب‌ها').click()
                    expect(page.get_by_role('button', name='+ افزودن به منتخب‌ها')).to_be_visible()
                    page.get_by_role('button', name='+ افزودن به منتخب‌ها').click()
                    assert page.goto(base + '/artists/?favorites=1').status == 200
                    expect(page.get_by_role('link').filter(has_text='بازیگر آزمایشی')).to_be_visible()
                    assert page.goto(base + '/artists/?q=هیچ‌کس&city=شیراز').status == 200
                    expect(page.get_by_text('رزومه‌ای پیدا نشد')).to_be_visible()
                    page.set_viewport_size({'width': 390, 'height': 844})
                    page.goto(base + '/artists/')
                    expect(page.get_by_role('heading', name='بازیگر آزمایشی', exact=True)).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                    if screenshots:
                        page.screenshot(path=str(screenshots / 'directory-mobile.png'), full_page=True)
                    page.goto(base + profile_path)
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                    logout()
                    login('qa_artist', artist_password)
                    page.goto(base + '/dashboard/edit/')
                    page.locator('#id_published').uncheck()
                    page.get_by_role('button', name='ذخیره', exact=True).click()
                    expect(page.locator('body')).to_contain_text('پیش‌نویس')
                    assert page.request.get(base + file_path).status == 200
                    logout()
                    login('qa_viewer', viewer_password)
                    assert page.request.get(base + profile_path).status == 403
                    assert page.request.get(base + file_path).status == 403
                    assert page.goto(base + '/artists/?favorites=1').status == 200
                    expect(page.get_by_text('رزومه‌ای پیدا نشد')).to_be_visible()
                    run_manage(environment, 'shell', '-c',
                        "from django.contrib.auth.models import User; from django.utils import timezone; "
                        "from portfolio.models import Entitlement,Favorite,PortfolioFile; "
                        "Entitlement.objects.filter(user__username='qa_viewer',kind='browse').update(ends_at=timezone.now())")
                    assert page.request.get(base + profile_path).status == 403
                    assert page.request.get(base + file_path).status == 403
                    assert page.goto(base + '/artists/?favorites=1').status == 403
                    run_manage(environment, 'shell', '-c',
                        "from portfolio.models import Favorite,PortfolioFile; "
                        "assert Favorite.objects.filter(user__username='qa_viewer').exists(); "
                        "assert PortfolioFile.objects.count()==2; "
                        "assert all(f.file.storage.exists(f.file.name) for f in PortfolioFile.objects.all())")
                    logout()
                    login('qa_artist', artist_password)
                    page.goto(base + '/dashboard/')
                    page.locator('.media-card').filter(has_text='ویدئوی آزمایشی').get_by_role(
                        'button', name='حذف فایل',
                    ).click()
                    run_manage(environment, 'shell', '-c',
                        "from portfolio.models import PortfolioFile; "
                        "from django.conf import settings; "
                        "assert PortfolioFile.objects.count()==1; "
                        "assert all(f.file.storage.exists(f.file.name) for f in PortfolioFile.objects.all()); "
                        "assert len([path for path in settings.MEDIA_ROOT.rglob('*') if path.is_file()])==1")
                    assert page.request.get(base + file_path).status == 200
                    assert page.request.get(base + video_path).status == 404
                    if errors:
                        raise AssertionError('\n'.join(errors))
                except BaseException as error:
                    failures = cleanup_steps([
                        ('browser context', context.close if context is not None else lambda: None),
                        ('browser', browser.close),
                    ])
                    report_cleanup_failures(failures, error)
                    raise
                else:
                    failures = cleanup_steps([
                        ('browser context', context.close if context is not None else lambda: None),
                        ('browser', browser.close),
                    ])
                    report_cleanup_failures(failures, None)
            run_manage(environment, 'backup_site', str(work / 'snapshot'))
            run_manage(environment, 'verify_backup', str(work / 'snapshot'))
            restored = work / 'restored'
            restored.mkdir()
            shutil.copyfile(work / 'snapshot' / 'db.sqlite3', restored / 'db.sqlite3')
            shutil.copytree(work / 'snapshot' / 'private-media', restored / 'private-media')
            restore_env = environment | {'DATA_ROOT': str(restored), 'PRIVATE_MEDIA_ROOT': str(restored / 'private-media')}
            run_manage(restore_env, 'check')
            run_manage(restore_env, 'shell', '-c',
                "from portfolio.models import Profile,PortfolioFile,Invitation,InvitationLink; "
                "assert Profile.objects.count()==3; assert Invitation.objects.count()==2; "
                "assert InvitationLink.objects.count()==3; f=PortfolioFile.objects.get(); "
                "assert f.file.open('rb').read(8)==b'\\x89PNG\\r\\n\\x1a\\n'")
            print(f'PASS: invited browser signup, invitation copy ({copy_result}), dashboard/privacy/deactivation, profile edit, private image and browser-recorded H.264 MP4 playback ({playback}), external-link lifecycle, paywall, paid browsing, favorites, mobile, backup and restored data.')
        finally:
            primary_error = sys.exc_info()[1]
            steps = []
            if server is not None:
                steps.append(('QA server shutdown', lambda: stop_server(server)))
            if server_log is not None:
                steps.append(('QA server log close', server_log.close))
            report_cleanup_failures(cleanup_steps(steps), primary_error)

if __name__ == '__main__':
    main()
