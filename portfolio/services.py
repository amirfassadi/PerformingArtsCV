from django.core.exceptions import ValidationError
from django.db import models, transaction
from .access import storage_quota, storage_used
from .models import PortfolioFile, Profile

def add_file(profile, uploaded, title):
    item = PortfolioFile(profile=profile, title=title, size=uploaded.size,
                         content_type=uploaded.detected_content_type)
    saved_name = None
    try:
        with transaction.atomic():
            # The write also serializes concurrent quota checks on SQLite.
            Profile.objects.filter(pk=profile.pk).update(updated_at=models.F('updated_at'))
            Profile.objects.select_for_update().get(pk=profile.pk)
            if storage_used(profile) + uploaded.size > storage_quota(profile.user):
                raise ValidationError('فضای کافی ندارید. یک فایل را حذف کنید یا پلن فضای بیشتر بگیرید.')
            item.file.save(uploaded.name, uploaded, save=False)
            saved_name = item.file.name
            item.full_clean()
            item.save()
    except Exception:
        if saved_name:
            item.file.storage.delete(saved_name)
        raise
    return item

def remove_file(item):
    with transaction.atomic():
        Profile.objects.filter(pk=item.profile_id).update(updated_at=models.F('updated_at'))
        item.delete()
