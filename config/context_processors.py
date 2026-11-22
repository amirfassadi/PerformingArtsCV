"""Tie the CSS URL to its contents so a release cannot reuse stale styling."""
from hashlib import sha256
from pathlib import Path

ASSET_VERSION = sha256(
    (Path(__file__).resolve().parent.parent / 'static' / 'app.css').read_bytes()
).hexdigest()[:16]


def assets(request):
    return {'asset_version': ASSET_VERSION}
