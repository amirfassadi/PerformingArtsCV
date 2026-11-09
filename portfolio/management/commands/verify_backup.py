import json
import sqlite3
from contextlib import closing
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from .backup_site import digest

class Command(BaseCommand):
    help = 'Verify snapshot hashes, SQLite integrity and media references without changing live data.'

    def add_arguments(self, parser):
        parser.add_argument('snapshot')

    def handle(self, *args, **options):
        root = Path(options['snapshot']).resolve()
        try:
            manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
            if manifest.get('version') != 1:
                raise ValueError('Unsupported snapshot version')
            indexed = set()
            for entry in manifest['files']:
                path = (root / entry['path']).resolve()
                if root not in path.parents or not path.is_file() or digest(path) != entry['sha256']:
                    raise ValueError('Missing, modified or invalid snapshot file')
                indexed.add(entry['path'])
            if 'db.sqlite3' not in indexed:
                raise ValueError('Database missing from manifest')
            with closing(sqlite3.connect((root / 'db.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('SQLite integrity check failed')
                if db.execute('PRAGMA foreign_key_check').fetchone():
                    raise ValueError('Database foreign key check failed')
                for name, size in db.execute('SELECT file, size FROM portfolio_portfoliofile'):
                    relative = (Path('private-media') / name).as_posix()
                    path = (root / relative).resolve()
                    if root not in path.parents or relative not in indexed or path.stat().st_size != size:
                        raise ValueError('A database media reference is missing or has the wrong size')
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            raise CommandError(f'Invalid backup: {error}') from error
        self.stdout.write(self.style.SUCCESS('Backup verified: checksums, database and media references are valid.'))
