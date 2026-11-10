import hashlib
import time
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.utils import OperationalError
from django.utils import timezone

from .models import RequestThrottle


def request_identity(request):
    # Do not accept client-controlled forwarding headers as identity.
    return request.META.get('REMOTE_ADDR') or 'unknown'


def rate_limit(request, action, limit=None, window_seconds=None):
    limit = limit or int(getattr(settings, f'{action.upper()}_RATE_LIMIT', 10))
    window_seconds = window_seconds or int(getattr(settings, f'{action.upper()}_RATE_WINDOW', 900))
    raw_key = f'{action}:{request_identity(request)}'
    key = hashlib.sha256(raw_key.encode()).hexdigest()
    now = timezone.now()
    for attempt in range(8):
        try:
            with transaction.atomic():
                row, _ = RequestThrottle.objects.select_for_update().get_or_create(
                    key=key, defaults={'window_started': now, 'attempts': 0},
                )
                if now - row.window_started >= timedelta(seconds=window_seconds):
                    row.window_started, row.attempts = now, 0
                allowed = row.attempts < limit
                if allowed:
                    row.attempts += 1
                row.save(update_fields=['window_started', 'attempts'])
                retry_after = max(1, window_seconds - int((now - row.window_started).total_seconds()))
                return allowed, retry_after
        except (IntegrityError, OperationalError):
            if attempt == 7:
                return False, window_seconds
            time.sleep(0.05 * (attempt + 1))
