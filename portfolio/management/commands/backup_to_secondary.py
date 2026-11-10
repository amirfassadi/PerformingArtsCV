import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create, verify and atomically publish a snapshot in a second local destination.'

    def add_arguments(self, parser):
        parser.add_argument('destination')

    def handle(self, *args, **options):
        destination = Path(options['destination']).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        if destination == media_root or media_root in destination.parents:
            raise CommandError('Secondary backup destination must be outside private media.')
        destination.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        final = destination / f'snapshot-{stamp}-{uuid.uuid4().hex[:8]}'
        staging = destination / f'.staging-{uuid.uuid4().hex}'
        try:
            management.call_command('backup_site', str(staging), stdout=self.stdout, stderr=self.stderr)
            management.call_command('verify_backup', str(staging), stdout=self.stdout, stderr=self.stderr)
            staging.replace(final)
        except Exception as error:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            raise CommandError(f'Secondary backup was not published: {error}') from error
        self.stdout.write(self.style.SUCCESS(f'Secondary backup published: {final}'))
