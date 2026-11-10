from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from .billing import start_payment, verify_payment
from .gateway import GatewayError
from .models import Payment, Plan

@never_cache
@login_required
def checkout(request, pk):
    plan = get_object_or_404(Plan, pk=pk, active=True, price_rial__gt=0)
    terms = [plan.pk, plan.name, plan.price_rial, plan.kind, plan.storage_mb, plan.duration_days]
    if request.method == 'POST':
        try:
            quote = signing.loads(request.POST.get('quote', ''), salt='checkout', max_age=900)
        except signing.BadSignature:
            quote = None
        if quote != terms:
            messages.error(request, 'اطلاعات پلن تغییر کرده یا زمان تأیید گذشته است. مبلغ را دوباره بررسی کن.')
            return redirect('checkout', pk=pk)
        try:
            return redirect(start_payment(request.user, plan))
        except GatewayError as error:
            messages.error(request, str(error))
            return redirect('plans')
    return render(request, 'portfolio/checkout.html', {
        'plan': plan, 'gateway_ready': bool(settings.ZARINPAL_MERCHANT_ID),
        'sandbox': settings.ZARINPAL_SANDBOX,
        'quote': signing.dumps(terms, salt='checkout'),
    })

@never_cache
@require_GET
def callback(request, pk):
    # The bank callback may arrive without the purchaser's browser session.
    payment = get_object_or_404(Payment, pk=pk)
    if not payment.authority or request.GET.get('Authority') != payment.authority:
        return HttpResponse('شناسه پرداخت معتبر نیست.', status=400)
    callback_status = request.GET.get('Status')
    if callback_status == 'OK':
        try:
            verify_payment(payment)
        except GatewayError:
            Payment.objects.filter(
                pk=payment.pk,
                status__in=(Payment.Status.PENDING, Payment.Status.UNKNOWN, Payment.Status.CANCELED),
            ).update(status=Payment.Status.UNKNOWN)
    elif callback_status == 'NOK':
        Payment.objects.filter(
            pk=payment.pk,
            status__in=(Payment.Status.PENDING, Payment.Status.UNKNOWN),
        ).update(status=Payment.Status.UNKNOWN)
    else:
        Payment.objects.filter(
            pk=payment.pk,
            status__in=(Payment.Status.PENDING, Payment.Status.UNKNOWN, Payment.Status.CANCELED),
        ).update(status=Payment.Status.UNKNOWN)
    return redirect('payment-detail', pk=pk)

@never_cache
@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    return render(request, 'portfolio/payment.html', {'payment': payment})

@never_cache
@login_required
@require_POST
def retry_verification(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    try:
        verify_payment(payment)
    except GatewayError as error:
        messages.error(request, str(error))
    return redirect('payment-detail', pk=pk)
