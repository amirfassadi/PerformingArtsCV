import secrets
import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

MB = 1_000_000

class SiteSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    free_storage_mb = models.PositiveIntegerField('سهمیه رایگان هر حساب (مگابایت)', default=100)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'
        constraints = [models.CheckConstraint(condition=Q(id=1), name='single_site_settings')]

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def __str__(self):
        return 'تنظیمات سهمیه رایگان'

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField('نام هنری', max_length=120)
    city = models.CharField('شهر', max_length=80, blank=True)
    specialty = models.CharField('تخصص', max_length=100, blank=True)
    skills = models.CharField('مهارت‌ها', max_length=300, blank=True)
    biography = models.TextField('معرفی', max_length=4000, blank=True)
    experience = models.TextField('سوابق حرفه‌ای', max_length=6000, blank=True)
    contact = models.CharField('راه ارتباط حرفه‌ای', max_length=200, blank=True)
    published = models.BooleanField('نمایش به مشترکان جست‌وجو', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'رزومه'
        verbose_name_plural = 'رزومه‌ها'

    def __str__(self):
        return self.display_name

def generate_invitation_token():
    return secrets.token_urlsafe(32)

class InvitationLink(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitation_link',
        verbose_name='صاحب لینک',
    )
    token = models.CharField(max_length=64, unique=True, default=generate_invitation_token, editable=False)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField('آخرین ثبت‌نام موفق', null=True, blank=True)

    class Meta:
        verbose_name = 'لینک دعوت'
        verbose_name_plural = 'لینک‌های دعوت'

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).values('user_id', 'token').first()
            if original and (original['user_id'] != self.user_id or original['token'] != self.token):
                raise ValidationError('صاحب لینک و شناسه آن پس از ایجاد قابل تغییر نیستند.')
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'دعوت‌های {self.user}'

class Invitation(models.Model):
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_invitations',
        verbose_name='دعوت‌کننده',
    )
    invitee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitation',
        verbose_name='دعوت‌شده',
    )
    link = models.ForeignKey(
        InvitationLink,
        on_delete=models.PROTECT,
        related_name='registrations',
        verbose_name='لینک استفاده‌شده',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'رابطه دعوت'
        verbose_name_plural = 'روابط دعوت'
        ordering = ['-created_at']

    def clean(self):
        if self.link_id and self.inviter_id != self.link.user_id:
            raise ValidationError({'inviter': 'دعوت‌کننده باید صاحب لینک استفاده‌شده باشد.'})

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).values('inviter_id', 'invitee_id', 'link_id').first()
            if original and any(original[field] != getattr(self, field) for field in ('inviter_id', 'invitee_id', 'link_id')):
                raise ValidationError('رابطه دعوت پس از ثبت قابل تغییر نیست.')
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def invitee_display_name(self):
        try:
            return self.invitee.profile.display_name
        except Profile.DoesNotExist:
            return 'نام ثبت نشده'

    def __str__(self):
        return f'{self.inviter} ← {self.invitee}'

class WorkLink(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='links')
    title = models.CharField('عنوان اثر', max_length=120)
    url = models.URLField('لینک اثر', max_length=1000)

    class Meta:
        ordering = ['id']
        verbose_name = 'لینک اثر'
        verbose_name_plural = 'لینک آثار'

    def __str__(self):
        return self.title

def private_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f'{instance.profile_id}/{instance.pk}{suffix}'

class PortfolioFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='files')
    title = models.CharField('عنوان نمونه‌کار', max_length=120)
    file = models.FileField(upload_to=private_upload_path)
    size = models.PositiveBigIntegerField(editable=False)
    content_type = models.CharField(max_length=60, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'فایل نمونه‌کار'
        verbose_name_plural = 'فایل‌های نمونه‌کار'

    @property
    def is_video(self):
        return self.content_type.startswith('video/')

    def __str__(self):
        return self.title

class Plan(models.Model):
    class Kind(models.TextChoices):
        BROWSE = 'browse', 'دسترسی به رزومه‌ها'
        STORAGE = 'storage', 'فضای ذخیره‌سازی'

    name = models.CharField('نام پلن', max_length=100)
    kind = models.CharField('نوع', max_length=10, choices=Kind.choices)
    storage_mb = models.PositiveIntegerField('سهمیه کل فضای پلن (مگابایت)', default=0)
    duration_days = models.PositiveIntegerField('مدت (روز)', default=30, validators=[MinValueValidator(1)])
    price_rial = models.PositiveBigIntegerField('قیمت (ریال)', default=0)
    active = models.BooleanField('قابل نمایش', default=True)

    class Meta:
        verbose_name = 'پلن'
        verbose_name_plural = 'پلن‌ها'
        constraints = [models.CheckConstraint(
            condition=Q(kind='browse', storage_mb=0) | Q(kind='storage', storage_mb__gt=0),
            name='plan_kind_matches_storage',
        )]

    def __str__(self):
        return self.name

class Entitlement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entitlements')
    kind = models.CharField('نوع دسترسی', max_length=10, choices=Plan.Kind.choices)
    storage_mb = models.PositiveIntegerField('سهمیه کل (مگابایت)', default=0)
    starts_at = models.DateTimeField('شروع', default=timezone.now)
    ends_at = models.DateTimeField('پایان')
    revoked = models.BooleanField('لغو شده', default=False)
    is_test = models.BooleanField('فعال‌سازی آزمایشی', default=False)
    reference = models.CharField('مرجع فعال‌سازی / پرداخت', max_length=200)

    class Meta:
        verbose_name = 'اشتراک فعال‌شده'
        verbose_name_plural = 'اشتراک‌های فعال‌شده'
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gt=models.F('starts_at')), name='entitlement_valid_dates'),
            models.CheckConstraint(
                condition=Q(kind='browse', storage_mb=0) | Q(kind='storage', storage_mb__gt=0),
                name='entitlement_kind_matches_storage',
            ),
        ]

    def __str__(self):
        return f'{self.user} / {self.get_kind_display()}'

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'profile'], name='unique_favorite')]

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار تأیید'
        PAID = 'paid', 'تأیید شده'
        FAILED = 'failed', 'ناموفق'
        CANCELED = 'canceled', 'لغوشده'
        UNKNOWN = 'unknown', 'نامشخص'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    plan_name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=Plan.Kind.choices)
    storage_mb = models.PositiveIntegerField(default=0)
    duration_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    amount_rial = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    sandbox = models.BooleanField(default=True)
    authority = models.CharField(max_length=64, unique=True, null=True, blank=True)
    ref_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    entitlement = models.OneToOneField(Entitlement, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        constraints = [models.UniqueConstraint(fields=['sandbox', 'ref_id'], name='unique_gateway_receipt')]

    def __str__(self):
        return f'{self.user} / {self.plan_name} / {self.get_status_display()}'
