"""Verify concurrent quota enforcement against a real, isolated SQLite file."""
import io
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    with tempfile.TemporaryDirectory(prefix='performingartscv-concurrency-') as temporary:
        os.environ.update({
            'DJANGO_SETTINGS_MODULE': 'config.settings', 'DJANGO_DEBUG': '1',
            'DATA_ROOT': temporary, 'PRIVATE_MEDIA_ROOT': str(Path(temporary) / 'media'),
            'ZARINPAL_MERCHANT_ID': '',
        })
        import django
        django.setup()
        from django.contrib.auth.models import User
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.core.management import call_command
        from django.db import connections
        from portfolio.access import storage_used
        from portfolio.models import Profile, SiteSettings
        from portfolio.services import add_file
        call_command('migrate', verbosity=0, stdout=io.StringIO())
        user = User.objects.create_user('isolated-concurrency-test')
        profile = Profile.objects.create(user=user, display_name='Quota test')
        SiteSettings.objects.create(free_storage_mb=1)
        barrier = Barrier(2)

        def worker(index):
            try:
                upload = SimpleUploadedFile(f'{index}.png', b'\x89PNG\r\n\x1a\n' + b'0' * 600000)
                upload.detected_content_type = 'image/png'
                barrier.wait(timeout=10)
                try:
                    add_file(profile, upload, f'Concurrent file {index}')
                    return 'saved'
                except ValidationError:
                    return 'quota-denied'
            finally:
                connections.close_all()

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(worker, range(2)))
            assert sorted(results) == ['quota-denied', 'saved'], results
            assert profile.files.count() == 1
            assert storage_used(profile) <= 1_000_000
            assert len(list((Path(temporary) / 'media').rglob('*.png'))) == 1
            print('PASS: two concurrent uploads cannot exceed one account quota; no extra file remains.')
        finally:
            connections.close_all()

if __name__ == '__main__':
    main()
