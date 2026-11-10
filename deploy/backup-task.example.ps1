$ErrorActionPreference = 'Stop'
$app = 'C:\srv\performingartscv\app'
$python = 'C:\srv\performingartscv\venv\Scripts\python.exe'
$destination = 'D:\performingartscv-secondary-backups'
Set-Location $app
& $python manage.py healthcheck
if ($LASTEXITCODE -ne 0) { throw 'Healthcheck failed; backup was not started.' }
& $python manage.py backup_to_secondary $destination
if ($LASTEXITCODE -ne 0) { throw 'Secondary backup failed.' }
