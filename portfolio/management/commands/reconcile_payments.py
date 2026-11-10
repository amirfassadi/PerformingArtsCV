from django.core.management.base import BaseCommand
from django.db import transaction

from portfolio.billing import verify_payment
from portfolio.gateway import GatewayError
from portfolio.models import Payment


class Command(BaseCommand):
    help = 'List or re-check payments that have not reached a final state.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Ask the gateway to verify each pending or unknown payment.',
        )

    def handle(self, *args, **options):
        payments = Payment.objects.filter(
            status__in=(Payment.Status.PENDING, Payment.Status.UNKNOWN),
        ).order_by('created_at')
        count = payments.count()
        if not options['verify']:
            for payment in payments:
                self.stdout.write(
                    f'{payment.pk} {payment.status} {payment.amount_rial} '
                    f'{payment.plan_name} {payment.user_id}',
                )
            self.stdout.write(f'{count} unresolved payment(s).')
            return

        verified = failed = 0
        for payment in payments:
            try:
                with transaction.atomic():
                    verify_payment(payment)
            except GatewayError as error:
                failed += 1
                self.stdout.write(self.style.WARNING(f'{payment.pk}: {error}'))
            else:
                verified += 1
                self.stdout.write(self.style.SUCCESS(f'{payment.pk}: paid'))
        self.stdout.write(f'Reconciled {verified} payment(s); {failed} still unresolved.')
