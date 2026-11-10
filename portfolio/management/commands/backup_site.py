import hashlib
import json
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone
from portfolio.models import PortfolioFile, SiteSettings

def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

class Command(BaseCommand):
    help = 'Create a consistent SQLite + private-media snapshot in a new directory.'

    def add_arguments(self, parser):
        parser.add_argument('destination')

    def handle(self, *args, **options):
        destination = Path(options['destination']).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        if destination == media_root or media_root in destination.parents:
            raise CommandError('Backup destination must be outside private media.')
        if destination.exists():
            raise CommandError('Destination already exists; choose a new snapshot directory.')
        if connection.vendor != 'sqlite':
            raise CommandError('This snapshot command currently supports SQLite only.')
        SiteSettings.current()
        destination.mkdir(parents=True)
        entries = []
        with transaction.atomic():
            # Hold SQLite's writer reservation while copying referenced media.
            SiteSettings.objects.filter(pk=1).update(free_storage_mb=F('free_storage_mb'))
            db_target = destination / 'db.sqlite3'
            source = connection.connection
            if source is None:
                raise CommandError('SQLite connection is not available for backup.')
            database_name = str(connection.settings_dict['NAME'])
            if database_name == ':memory:' or database_name.startswith('file:'):
                db_target.write_bytes(source.serialize())
            else:
                with closing(sqlite3.connect(database_name)) as source_file:
                    with closing(sqlite3.connect(db_target)) as target:
                        source_file.backup(target)
            entries.append({'path': 'db.sqlite3', 'sha256': digest(db_target)})
            for item in PortfolioFile.objects.all().iterator():
                original = (media_root / item.file.name).resolve()
                if media_root not in original.parents or not original.is_file():
                    raise CommandError(f'Missing or invalid media: {item.pk}; snapshot is incomplete.')
                relative = Path('private-media') / item.file.name
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, target)
                entries.append({'path': relative.as_posix(), 'sha256': digest(target)})
        manifest = {'version': 1, 'created_at': timezone.now().isoformat(), 'files': entries}
        (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Backup complete: {destination} ({len(entries)} files)'))
