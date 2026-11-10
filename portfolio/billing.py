from datetime import timedelta
from django.conf import settings
from django.db import models, transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from .gateway import GatewayError, Zarinpal
from .models import Entitlement, Payment, Profile

def start_payment(user, plan):
    if plan.price_rial <= 0 or not settings.ZARINPAL_MERCHANT_ID:
        raise GatewayError('این پلن فعلاً برای خرید آنلاین آماده نیست.')
    payment = Payment.objects.create(
        user=user, plan=plan, plan_name=plan.name, kind=plan.kind,
        storage_mb=plan.storage_mb, duration_days=plan.duration_days,
        amount_rial=plan.price_rial, sandbox=settings.ZARINPAL_SANDBOX,
    )
    gateway = Zarinpal(sandbox=payment.sandbox)
    callback_url = settings.PUBLIC_BASE_URL + reverse('payment-callback', args=[payment.pk])
    try:
        payment.authority = gateway.request(payment, callback_url)
    except GatewayError:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=['status'])
        raise
    payment.save(update_fields=['authority'])
    return gateway.start_url(payment.authority)

def verify_payment(payment):
    if payment.status == Payment.Status.PAID:
        return payment
    if payment.status in (Payment.Status.CANCELED, Payment.Status.FAILED):
        raise GatewayError('این سفارش دیگر قابل تأیید نیست؛ سفارش تازه‌ای ایجاد کنید.')
    if not payment.authority:
        raise GatewayError('درخواست معتبری برای این پرداخت وجود ندارد.')
    receipt = Zarinpal(sandbox=payment.sandbox).verify(payment)
    with transaction.atomic():
        # Lock the account before reading payment state: also works on SQLite.
        Profile.objects.filter(user_id=payment.user_id).update(updated_at=models.F('updated_at'))
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.status == Payment.Status.PAID:
            return payment
        now = timezone.now()
        latest_end = Entitlement.objects.filter(
            user=payment.user, kind=payment.kind, storage_mb=payment.storage_mb,
            revoked=False, ends_at__gt=now, is_test=payment.sandbox,
        ).aggregate(latest=Max('ends_at'))['latest']
        start = max(now, latest_end) if latest_end else now
        payment.entitlement = Entitlement.objects.create(
            user=payment.user, kind=payment.kind, storage_mb=payment.storage_mb,
            starts_at=start, ends_at=start + timedelta(days=payment.duration_days),
            is_test=payment.sandbox,
            reference=f'zarinpal:{"sandbox" if payment.sandbox else "live"}:{receipt}',
        )
        payment.ref_id = receipt
        payment.status = Payment.Status.PAID
        payment.verified_at = now
        payment.save(update_fields=['entitlement', 'ref_id', 'status', 'verified_at'])
    return payment
