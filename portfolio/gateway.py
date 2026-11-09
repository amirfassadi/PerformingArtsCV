"""Zarinpal v4 adapter. Never accept an amount or destination from the browser."""
import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen
from django.conf import settings

class GatewayError(Exception):
    pass

class Zarinpal:
    def __init__(self, sandbox=None):
        self.sandbox = settings.ZARINPAL_SANDBOX if sandbox is None else sandbox
        self.base = 'https://sandbox.zarinpal.com' if self.sandbox else 'https://payment.zarinpal.com'

    def call(self, action, payload):
        if not settings.ZARINPAL_MERCHANT_ID:
            raise GatewayError('درگاه پرداخت هنوز تنظیم نشده است.')
        payload = {'merchant_id': settings.ZARINPAL_MERCHANT_ID, **payload}
        request = Request(
            f'{self.base}/pg/v4/payment/{action}.json',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, method='POST',
        )
        try:
            with urlopen(request, timeout=15) as response:
                body = json.loads(response.read(65536))
            data = body.get('data') if isinstance(body, dict) else None
            if not isinstance(data, dict):
                raise GatewayError('درگاه پرداخت پاسخ معتبر نداد؛ دوباره تلاش کنید.')
            return data
        except (URLError, TimeoutError, ValueError, OSError) as exc:
            raise GatewayError('ارتباط با درگاه برقرار نشد. وضعیت پرداخت هنوز تأیید نشده است.') from exc

    def request(self, payment, callback_url):
        data = self.call('request', {
            'amount': payment.amount_rial, 'currency': 'IRR',
            'description': f'صحنه‌نما — {payment.plan_name}', 'callback_url': callback_url,
            'metadata': {'order_id': str(payment.pk)},
        })
        authority = data.get('authority', '')
        prefix = 'S' if self.sandbox else 'A'
        if data.get('code') != 100 or not isinstance(authority, str) or not re.fullmatch(prefix + r'[A-Za-z0-9]{20,63}', authority):
            raise GatewayError('درگاه درخواست پرداخت را نپذیرفت؛ بعداً دوباره تلاش کنید.')
        return authority

    def start_url(self, authority):
        return f'{self.base}/pg/StartPay/{authority}'

    def verify(self, payment):
        data = self.call('verify', {'amount': payment.amount_rial, 'authority': payment.authority})
        receipt = str(data.get('ref_id', ''))
        if data.get('code') not in (100, 101) or not receipt.isdigit() or int(receipt) <= 0 or len(receipt) > 100:
            raise GatewayError('پرداخت توسط درگاه تأیید نشد. در صورت کسر وجه، با پشتیبانی پیگیری کنید.')
        return receipt
