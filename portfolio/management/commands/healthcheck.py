import shutil
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Check database integrity, private-media availability and free disk space.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-free-bytes',
            type=int,
            default=int(getattr(settings, 'HEALTHCHECK_MIN_FREE_BYTES', 100 * 1024 * 1024)),
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists() or not media_root.is_dir():
            raise CommandError('Private media root is missing or is not a directory.')
        if connection.vendor != 'sqlite':
            raise CommandError('Healthcheck currently supports SQLite only.')
        try:
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA integrity_check')
                integrity = cursor.fetchone()[0]
                cursor.execute('PRAGMA foreign_key_check')
                foreign_key = cursor.fetchone()
        except DatabaseError as error:
            raise CommandError(f'Database health check failed: {error}') from error
        if integrity != 'ok' or foreign_key:
            raise CommandError('Database integrity or foreign-key check failed.')
        free_bytes = shutil.disk_usage(media_root).free
        if free_bytes < options['min_free_bytes']:
            raise CommandError(
                f'Free disk space {free_bytes} is below required {options["min_free_bytes"]} bytes.',
            )
        self.stdout.write(self.style.SUCCESS(
            f'Healthcheck passed: sqlite={integrity}, media={media_root}, free_bytes={free_bytes}.',
        ))
