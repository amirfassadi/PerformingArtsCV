from django.conf import settings
from django.db.models import Max, Sum
from django.utils import timezone
from .models import MB, Entitlement, Plan, SiteSettings

def active_entitlements(user):
    now = timezone.now()
    grants = Entitlement.objects.filter(user=user, revoked=False, starts_at__lte=now, ends_at__gt=now)
    if not settings.ZARINPAL_SANDBOX:
        grants = grants.filter(is_test=False)
    return grants

def can_browse(user):
    return user.is_authenticated and active_entitlements(user).filter(kind=Plan.Kind.BROWSE).exists()

def can_view_profile(user, profile):
    return user.is_authenticated and (
        profile.user_id == user.pk or (profile.published and can_browse(user))
    )

def storage_quota(user):
    free = SiteSettings.current().free_storage_mb
    paid = active_entitlements(user).filter(kind=Plan.Kind.STORAGE).aggregate(limit=Max('storage_mb'))['limit'] or 0
    return max(free, paid) * MB

def storage_used(profile):
    return profile.files.aggregate(total=Sum('size'))['total'] or 0
