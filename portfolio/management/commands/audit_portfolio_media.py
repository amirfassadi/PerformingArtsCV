import posixpath
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from portfolio.models import PortfolioFile


class Command(BaseCommand):
    help = 'Report missing, untracked, or size-mismatched private portfolio files without changing data.'

    def handle(self, *args, **options):
        try:
            stored_names = self._stored_names()
        except NotImplementedError as error:
            raise CommandError('The configured file storage does not support directory listing.') from error

        records = list(PortfolioFile.objects.order_by('pk').values('pk', 'file', 'size'))
        referenced_names = {record['file'] for record in records if record['file']}
        missing = []
        mismatched = []
        for record in records:
            name = record['file']
            if not name or name not in stored_names:
                missing.append(record)
                continue
            actual_size = default_storage.size(name)
            if actual_size != record['size']:
                mismatched.append((record, actual_size))

        orphaned = sorted(stored_names - referenced_names)
        self.stdout.write(
            f'Media audit: {len(records)} database records, {len(stored_names)} stored files, '
            f'{len(missing)} missing, {len(orphaned)} untracked, {len(mismatched)} size mismatch(es).'
        )
        for record in missing:
            self.stdout.write(f'MISSING record={record["pk"]} name={record["file"] or "(empty)"}')
        for name in orphaned:
            self.stdout.write(f'UNTRACKED name={name}')
        for record, actual_size in mismatched:
            self.stdout.write(
                f'SIZE_MISMATCH record={record["pk"]} name={record["file"]} '
                f'recorded={record["size"]} actual={actual_size}'
            )
        if missing or orphaned or mismatched:
            raise CommandError('Discrepancies found; no records or files were changed. Reconcile manually after review.')
        self.stdout.write('No discrepancies found; no data was changed.')

    @staticmethod
    def _stored_names():
        names = set()
        directories = ['']
        while directories:
            directory = directories.pop()
            try:
                child_directories, files = default_storage.listdir(directory)
            except FileNotFoundError:
                if not directory:
                    return names
                raise
            names.update(posixpath.join(directory, name) if directory else name for name in files)
            directories.extend(
                posixpath.join(directory, name) if directory else name
                for name in child_directories
            )
        return names
