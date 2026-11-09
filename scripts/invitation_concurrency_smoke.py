"""Verify simultaneous signups can safely reuse one invitation in file-backed SQLite."""
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def verify_concurrent_signups(call_command, connections, Client, reverse, User, Invitation, InvitationLink, Profile):
    call_command('migrate', verbosity=0)
    inviter = User.objects.create_user('parallel-inviter')
    link = inviter.invitation_link
    barrier = Barrier(2)

    def register(index):
        connections.close_all()
        client = Client()
        try:
            barrier.wait(timeout=10)
            response = client.post(reverse('signup-invitation', args=[link.token]), {
                'username': f'parallel-invitee-{index}',
                'email': f'parallel-{index}@example.invalid',
                'password1': 'Synthetic-parallel-password-1',
                'password2': 'Synthetic-parallel-password-1',
            })
            return response.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(register, (1, 2)))

    invitees = User.objects.filter(username__startswith='parallel-invitee-')
    assert statuses == [302, 302], statuses
    assert invitees.count() == 2
    assert Profile.objects.filter(user__in=invitees).count() == 2
    assert Invitation.objects.filter(link=link).count() == 2
    assert InvitationLink.objects.filter(user__in=invitees).count() == 2
    print('PASS: two concurrent registrations using one active link each created exactly one account, profile, invitation and personal link.')


def main():
    with tempfile.TemporaryDirectory(prefix='performingartscv-invitation-concurrency-') as temporary:
        os.environ.update({
            'DJANGO_SETTINGS_MODULE': 'config.settings',
            'DJANGO_DEBUG': '1',
            'DATA_ROOT': temporary,
            'PRIVATE_MEDIA_ROOT': str(Path(temporary) / 'private-media'),
            'ZARINPAL_MERCHANT_ID': '',
        })

        import django
        django.setup()

        from django.core.management import call_command
        from django.db import connections
        from django.test import Client
        from django.urls import reverse
        from django.contrib.auth.models import User
        from portfolio.models import Invitation, InvitationLink, Profile

        try:
            verify_concurrent_signups(
                call_command, connections, Client, reverse, User, Invitation, InvitationLink, Profile,
            )
        finally:
            connections.close_all()


if __name__ == '__main__':
    main()
