"""Verify the invitation migration preserves synthetic legacy accounts and relations."""
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def verify_legacy_data(connection, settings, call_command, timezone):
    from django.contrib.auth.hashers import make_password
    from django.db.migrations.executor import MigrationExecutor

    initial_target = [('portfolio', '0003_entitlement_is_test')]
    MigrationExecutor(connection).migrate(initial_target)
    old_apps = MigrationExecutor(connection).loader.project_state(initial_target).apps
    User = old_apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    Profile = old_apps.get_model('portfolio', 'Profile')
    Plan = old_apps.get_model('portfolio', 'Plan')
    Entitlement = old_apps.get_model('portfolio', 'Entitlement')
    Favorite = old_apps.get_model('portfolio', 'Favorite')
    Payment = old_apps.get_model('portfolio', 'Payment')

    artist = User.objects.create(
        username='legacy-artist',
        email='legacy-artist@example.invalid',
        password=make_password('Synthetic-legacy-password-1'),
    )
    viewer = User.objects.create(
        username='legacy-viewer',
        email='legacy-viewer@example.invalid',
        password=make_password('Synthetic-legacy-password-2'),
    )
    Profile.objects.create(user=artist, display_name='رزومه قدیمی', published=True)
    Profile.objects.create(user=viewer, display_name='بیننده قدیمی')
    plan = Plan.objects.create(name='Synthetic browse', kind='browse', duration_days=30, price_rial=1000)
    now = timezone.now()
    entitlement = Entitlement.objects.create(
        user=viewer, kind='browse', storage_mb=0, starts_at=now,
        ends_at=now + timedelta(days=30), reference='synthetic-legacy',
    )
    Favorite.objects.create(user=viewer, profile=Profile.objects.get(user=artist))
    Payment.objects.create(
        user=viewer, plan=plan, plan_name=plan.name, kind='browse', storage_mb=0,
        duration_days=30, amount_rial=1000, sandbox=True, authority='synthetic-legacy-authority',
        ref_id='synthetic-legacy-receipt', status='paid', entitlement=entitlement,
        verified_at=now,
    )
    original_hashes = dict(User.objects.values_list('username', 'password'))

    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())

    from django.contrib.auth import get_user_model
    from portfolio.models import Entitlement as CurrentEntitlement
    from portfolio.models import Favorite as CurrentFavorite
    from portfolio.models import Invitation, InvitationLink
    from portfolio.models import Payment as CurrentPayment
    from portfolio.models import Plan as CurrentPlan
    from portfolio.models import Profile as CurrentProfile

    CurrentUser = get_user_model()
    assert CurrentUser.objects.count() == 2
    assert dict(CurrentUser.objects.values_list('username', 'password')) == original_hashes
    assert CurrentProfile.objects.count() == 2
    assert CurrentProfile.objects.get(user__username='legacy-artist').display_name == 'رزومه قدیمی'
    assert CurrentPlan.objects.count() == 1
    assert CurrentEntitlement.objects.count() == 1
    assert CurrentFavorite.objects.count() == 1
    assert CurrentPayment.objects.count() == 1
    assert Invitation.objects.count() == 0
    links = list(InvitationLink.objects.order_by('user_id'))
    assert len(links) == 2
    assert {link.user_id for link in links} == set(CurrentUser.objects.values_list('pk', flat=True))
    assert len({link.token for link in links}) == 2
    assert all(len(link.token) >= 40 for link in links)
    call_command('check', verbosity=0)
    print('PASS: migration preserved two synthetic accounts and their profile, plan, entitlement, favorite, payment and password hashes; created unique links without fabricated invitations.')


def main():
    with tempfile.TemporaryDirectory(prefix='performingartscv-invitation-migration-') as temporary:
        os.environ.update({
            'DJANGO_SETTINGS_MODULE': 'config.settings',
            'DJANGO_DEBUG': '1',
            'DATA_ROOT': temporary,
            'PRIVATE_MEDIA_ROOT': str(Path(temporary) / 'private-media'),
            'ZARINPAL_MERCHANT_ID': '',
        })

        import django
        django.setup()

        from django.conf import settings
        from django.core.management import call_command
        from django.db import connection, connections
        from django.utils import timezone

        try:
            verify_legacy_data(connection, settings, call_command, timezone)
        finally:
            connections.close_all()


if __name__ == '__main__':
    main()
