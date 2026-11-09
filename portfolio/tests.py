import base64
import io
import json
import sqlite3
import tempfile
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .access import can_browse, storage_quota, storage_used
from .billing import start_payment, verify_payment
from .forms import UploadForm
from .gateway import GatewayError, Zarinpal
from .models import MB, Entitlement, Invitation, InvitationLink, Payment, Plan, PortfolioFile, Profile, SiteSettings
from .services import add_file

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')

class ProductTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('artist', password='Artist-strong-password!')
        cls.viewer = User.objects.create_user('viewer', password='Viewer-strong-password!')
        cls.artist = Profile.objects.create(user=cls.owner, display_name='هنرمند آزمایشی', published=True, city='تهران', specialty='بازیگر')
        cls.viewer_profile = Profile.objects.create(user=cls.viewer, display_name='انتخاب‌کننده')
        SiteSettings.current()

    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

    def grant(self, user=None, kind='browse', **kwargs):
        return Entitlement.objects.create(
            user=user or self.viewer, kind=kind, reference='test',
            ends_at=timezone.now() + timedelta(days=1), **kwargs,
        )

    def upload(self, user=None, payload=PNG):
        self.client.force_login(user or self.owner)
        return self.client.post(reverse('upload'), {
            'title': 'تصویر تست', 'file': SimpleUploadedFile('work.png', payload, 'image/png'),
        })

    def test_invited_signup_creates_one_profile_and_one_immutable_relation_without_rewards(self):
        response = self.client.post(reverse('signup-invitation', args=[self.owner.invitation_link.token]), {
            'username': 'new-artist', 'email': 'artist@example.test',
            'password1': 'Fresh-artist-password!', 'password2': 'Fresh-artist-password!',
        })
        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(username='new-artist')
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        invitation = Invitation.objects.get(invitee=user)
        self.assertEqual(invitation.inviter, self.owner)
        self.assertEqual(invitation.link, self.owner.invitation_link)
        self.assertEqual(InvitationLink.objects.filter(user=user).count(), 1)
        self.assertFalse(can_browse(user))
        self.assertEqual(storage_quota(user), 100 * MB)
        self.assertFalse(Entitlement.objects.filter(user=user).exists())
        self.assertFalse(Payment.objects.filter(user=user).exists())

    def test_signup_requires_a_valid_active_invitation(self):
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'ساخت حساب فقط از طریق لینک دعوت فعال ممکن است')

        invalid_path = reverse('signup-invitation', args=['unknown-token'])
        self.assertEqual(self.client.get(invalid_path).status_code, 404)
        response = self.client.post(invalid_path, {
            'username': 'no-invite', 'email': 'no-invite@example.test',
            'password1': 'Fresh-artist-password!', 'password2': 'Fresh-artist-password!',
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(User.objects.filter(username='no-invite').exists())

    def test_invited_signup_keeps_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        path = reverse('signup-invitation', args=[self.owner.invitation_link.token])
        response = client.get(path)
        self.assertEqual(response['Referrer-Policy'], 'strict-origin')
        csrf_token = client.cookies['csrftoken'].value
        data = {
            'username': 'csrf-invitee', 'email': 'csrf@example.test',
            'password1': 'Fresh-artist-password!', 'password2': 'Fresh-artist-password!',
        }

        self.assertEqual(client.post(path, data).status_code, 403)
        self.assertFalse(User.objects.filter(username='csrf-invitee').exists())
        self.assertEqual(client.post(path, data, HTTP_X_CSRFTOKEN=csrf_token).status_code, 302)

    def test_disabled_invitation_blocks_a_signup_posted_after_link_was_opened(self):
        link = self.owner.invitation_link
        path = reverse('signup-invitation', args=[link.token])
        self.assertEqual(self.client.get(path).status_code, 200)
        link.is_active = False
        link.save(update_fields=['is_active'])

        response = self.client.post(path, {
            'username': 'disabled-invite', 'email': 'disabled@example.test',
            'password1': 'Fresh-artist-password!', 'password2': 'Fresh-artist-password!',
        })
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'لینک دعوت معتبر نیست', status_code=404)
        self.assertFalse(User.objects.filter(username='disabled-invite').exists())
        self.assertFalse(Invitation.objects.filter(link=link).exists())

    def test_invitation_link_is_reusable_for_multiple_registrations(self):
        link = self.owner.invitation_link
        for username in ('invite-one', 'invite-two'):
            response = self.client.post(reverse('signup-invitation', args=[link.token]), {
                'username': username, 'email': f'{username}@example.test',
                'password1': 'Fresh-artist-password!', 'password2': 'Fresh-artist-password!',
            })
            self.assertRedirects(response, reverse('dashboard'))
            self.client.logout()

        self.assertEqual(Invitation.objects.filter(link=link).count(), 2)
        self.assertEqual(User.objects.get(username='invite-one').invitation.inviter, self.owner)
        self.assertEqual(User.objects.get(username='invite-two').invitation.inviter, self.owner)

    def test_existing_account_opening_a_link_does_not_create_an_invitation(self):
        link = self.owner.invitation_link
        self.client.force_login(self.viewer)
        response = self.client.get(reverse('signup-invitation', args=[link.token]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Invitation.objects.filter(invitee=self.viewer).exists())
        self.assertEqual(Profile.objects.filter(user=self.viewer).count(), 1)
        link.refresh_from_db()
        self.assertIsNone(link.last_used_at)

    def test_invitation_relationship_cannot_be_reassigned(self):
        link = self.owner.invitation_link
        invitee = User.objects.create_user('immutable-invitee', password='Invitee-strong-password!')
        invitation = Invitation.objects.create(inviter=self.owner, invitee=invitee, link=link)
        invitation.inviter = self.viewer
        with self.assertRaises(ValidationError):
            invitation.save()
        invitation.refresh_from_db()
        self.assertEqual(invitation.inviter, self.owner)

    def test_dashboard_shows_copyable_link_and_invitee_display_name_only(self):
        invitee = User.objects.create_user('private-invitee', email='private@example.test')
        Profile.objects.create(user=invitee, display_name='نام نمایشی دعوت‌شده')
        Invitation.objects.create(inviter=self.owner, invitee=invitee, link=self.owner.invitation_link)

        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, reverse('signup-invitation', args=[self.owner.invitation_link.token]))
        self.assertContains(response, 'نام نمایشی دعوت‌شده')
        self.assertNotContains(response, 'private@example.test')
        self.assertEqual(response.context['invite_count'], 1)

    def test_dashboard_does_not_offer_a_disabled_invitation_link(self):
        link = self.owner.invitation_link
        link.is_active = False
        link.save(update_fields=['is_active'])
        self.client.force_login(self.owner)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'لینک دعوت این حساب توسط مدیر غیرفعال شده است')
        self.assertNotContains(response, link.token)
        self.assertEqual(response.context['invite_count'], 0)

    def test_admin_can_inspect_invitations_and_disable_links(self):
        invitee = User.objects.create_user('admin-visible-invitee')
        Profile.objects.create(user=invitee, display_name='دعوت‌شده برای مدیر')
        link = self.owner.invitation_link
        Invitation.objects.create(inviter=self.owner, invitee=invitee, link=link)
        admin_user = User.objects.create_superuser('invitation-admin', email='admin@example.test', password='Admin-strong-password!')
        self.client.force_login(admin_user)

        self.assertContains(self.client.get(reverse('admin:portfolio_invitation_changelist')), 'دعوت‌شده برای مدیر')
        change_url = reverse('admin:portfolio_invitationlink_change', args=[link.pk])
        response = self.client.post(change_url, {'is_active': '', '_save': 'ذخیره'})
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertFalse(link.is_active)
        self.assertTrue(Invitation.objects.filter(invitee=invitee).exists())

    def test_anonymous_cannot_read_profile_or_directory(self):
        for path in [reverse('profile', args=[self.artist.pk]), reverse('directory')]:
            self.assertEqual(self.client.get(path).status_code, 302)

    def test_free_account_can_read_own_but_not_other_profile(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse('profile', args=[self.viewer_profile.pk])).status_code, 200)
        response = self.client.get(reverse('profile', args=[self.artist.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, self.artist.display_name, status_code=403)
        self.assertEqual(self.client.get(reverse('directory')).status_code, 403)

    def test_storage_purchase_does_not_grant_browse(self):
        self.grant(kind='storage', storage_mb=500)
        self.assertEqual(storage_quota(self.viewer), 500 * MB)
        self.assertFalse(can_browse(self.viewer))

    def test_browse_purchase_does_not_increase_storage(self):
        self.grant()
        self.assertTrue(can_browse(self.viewer))
        self.assertEqual(storage_quota(self.viewer), 100 * MB)

    def test_paid_viewer_searches_and_favorites(self):
        self.grant()
        self.client.force_login(self.viewer)
        response = self.client.get(reverse('directory'), {'q': 'بازیگر', 'city': 'تهران'})
        self.assertContains(response, self.artist.display_name)
        self.assertContains(self.client.get(reverse('profile', args=[self.artist.pk])), self.artist.display_name)
        self.assertEqual(self.client.post(reverse('favorite', args=[self.artist.pk])).status_code, 302)
        self.assertContains(self.client.get(reverse('directory'), {'favorites': '1'}), self.artist.display_name)

    def test_paid_viewer_cannot_read_draft(self):
        self.grant()
        self.artist.published = False
        self.artist.save()
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse('profile', args=[self.artist.pk])).status_code, 403)
        self.assertNotContains(self.client.get(reverse('directory')), self.artist.display_name)

    def test_expired_revoked_and_future_grants_do_not_allow_browse(self):
        now = timezone.now()
        grant = self.grant(starts_at=now - timedelta(days=2))
        for updates in [
            {'ends_at': now - timedelta(days=1)},
            {'starts_at': now + timedelta(hours=1), 'ends_at': now + timedelta(days=1)},
            {'starts_at': now - timedelta(hours=1), 'revoked': True},
        ]:
            Entitlement.objects.filter(pk=grant.pk).update(**updates)
            self.assertFalse(can_browse(self.viewer))

    @override_settings(ZARINPAL_SANDBOX=False)
    def test_sandbox_grant_is_not_valid_in_live_mode(self):
        self.grant(is_test=True)
        self.grant(kind='storage', storage_mb=1000, is_test=True)
        self.assertFalse(can_browse(self.viewer))
        self.assertEqual(storage_quota(self.viewer), 100 * MB)

    def test_owner_cannot_modify_another_profile_by_forged_form_field(self):
        self.client.force_login(self.viewer)
        self.client.post(reverse('edit-profile'), {'display_name': 'نام جدید', 'user': self.owner.pk})
        self.artist.refresh_from_db()
        self.assertEqual(self.artist.display_name, 'هنرمند آزمایشی')

    def test_free_quota_updates_existing_accounts_immediately(self):
        config = SiteSettings.current()
        config.free_storage_mb = 35
        config.save()
        self.assertEqual(storage_quota(self.owner), 35 * MB)

    def test_quota_is_total_not_sum_of_paid_plans(self):
        self.grant(kind='storage', storage_mb=200)
        self.grant(kind='storage', storage_mb=500)
        self.assertEqual(storage_quota(self.viewer), 500 * MB)

    def test_upload_stores_private_file_and_accounts_actual_bytes(self):
        self.assertEqual(self.upload().status_code, 302)
        item = PortfolioFile.objects.get()
        self.assertEqual(item.size, len(PNG))
        self.assertEqual(storage_used(self.artist), len(PNG))
        self.assertTrue(Path(item.file.path).is_file())
        self.assertEqual(self.client.get('/never-public/' + item.file.name).status_code, 404)

    def test_reject_upload_when_quota_full_without_saving_file(self):
        SiteSettings.objects.filter(pk=1).update(free_storage_mb=0)
        response = self.upload()
        self.assertContains(response, 'فضای کافی ندارید')
        self.assertFalse(PortfolioFile.objects.exists())
        self.assertEqual(list(Path(self.media.name).rglob('*.png')), [])

    def test_reject_next_upload_when_combined_size_exceeds_quota(self):
        SiteSettings.objects.filter(pk=1).update(free_storage_mb=1)
        self.assertEqual(self.upload(payload=PNG + b'0' * 600000).status_code, 302)
        self.assertContains(self.upload(payload=PNG + b'0' * 600000), 'فضای کافی ندارید')
        self.assertEqual(PortfolioFile.objects.count(), 1)

    @override_settings(MAX_UPLOAD_BYTES=32)
    def test_streaming_limit_rejects_large_upload(self):
        self.assertContains(self.upload(), 'حجم فایل از سقف مجاز')
        self.assertFalse(PortfolioFile.objects.exists())

    def test_fake_image_and_html_rejected(self):
        response = self.upload(payload=b'<html>not an image</html>')
        self.assertContains(response, 'فایل معتبر')
        self.assertFalse(PortfolioFile.objects.exists())

    def test_disk_write_is_cleaned_when_database_save_fails(self):
        form = UploadForm({'title': 'test'}, {'file': SimpleUploadedFile('a.png', PNG)})
        self.assertTrue(form.is_valid())
        with patch.object(PortfolioFile, 'save', side_effect=RuntimeError('DB failed')):
            with self.assertRaises(RuntimeError):
                add_file(self.artist, form.cleaned_data['file'], 'test')
        self.assertEqual(list(Path(self.media.name).rglob('*.png')), [])

    def test_file_authorization_and_byte_ranges(self):
        self.upload()
        item = PortfolioFile.objects.get()
        url = reverse('media', args=[item.pk])
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(url).status_code, 403)
        grant = self.grant()
        response = self.client.get(url, HTTP_RANGE='bytes=2-9')
        self.assertEqual(response.status_code, 206)
        self.assertEqual(b''.join(response.streaming_content), PNG[2:10])
        self.assertIn('no-store', response['Cache-Control'])
        response.close()
        response = self.client.get(url, HTTP_RANGE='bytes=-5')
        self.assertEqual(b''.join(response.streaming_content), PNG[-5:])
        response.close()
        self.assertEqual(self.client.get(url, HTTP_RANGE='bytes=900-999').status_code, 416)
        grant.revoked = True
        grant.save()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_viewer_cannot_delete_owner_file(self):
        self.upload()
        item = PortfolioFile.objects.get()
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(reverse('delete-file', args=[item.pk])).status_code, 404)
        self.assertTrue(PortfolioFile.objects.filter(pk=item.pk).exists())

    def test_owner_delete_frees_space_and_removes_blob(self):
        self.upload()
        item = PortfolioFile.objects.get()
        path = Path(item.file.path)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('delete-file', args=[item.pk]))
        self.assertEqual(storage_used(self.artist), 0)
        self.assertFalse(path.exists())

    def test_lowering_quota_keeps_files_readable(self):
        self.upload()
        SiteSettings.objects.filter(pk=1).update(free_storage_mb=0)
        item = PortfolioFile.objects.get()
        response = self.client.get(reverse('media', args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertContains(self.client.get(reverse('dashboard')), 'مصرف فعلی از سهمیه بیشتر است')

    def test_csrf_is_required_for_upload(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(reverse('upload'), {'title': 'unsafe'}).status_code, 403)

    def test_regular_user_cannot_change_site_quota(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get('/admin/portfolio/sitesettings/1/change/').status_code, 302)

    def test_staff_can_change_quota_from_admin(self):
        self.owner.is_staff = self.owner.is_superuser = True
        self.owner.save()
        self.client.force_login(self.owner)
        response = self.client.post('/admin/portfolio/sitesettings/1/change/', {'free_storage_mb': 250, '_save': 'Save'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(storage_quota(self.viewer), 250 * MB)

    def test_work_links_reject_javascript_urls(self):
        self.client.force_login(self.owner)
        self.client.post(reverse('add-link'), {'title': 'x', 'url': 'javascript:alert(1)'})
        self.assertFalse(self.artist.links.exists())

@override_settings(ZARINPAL_MERCHANT_ID='00000000-0000-0000-0000-000000000000', ZARINPAL_SANDBOX=True)
class BillingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('payer', password='Strong-password!')
        Profile.objects.create(user=self.user, display_name='payer')
        self.plan = Plan.objects.create(name='مشاهده ماهانه', kind='browse', price_rial=200000, duration_days=30)
        self.client.force_login(self.user)

    def payment(self, **overrides):
        defaults = dict(user=self.user, plan=self.plan, plan_name=self.plan.name, kind='browse',
                        duration_days=30, amount_rial=200000, authority='S' + '0' * 35)
        return Payment.objects.create(**(defaults | overrides))

    @patch.object(Zarinpal, 'call', return_value={'code': 100, 'authority': 'S' + '1' * 35})
    def test_checkout_uses_server_price_and_saved_plan_snapshot(self, call):
        quote = self.client.get(reverse('checkout', args=[self.plan.pk])).context['quote']
        response = self.client.post(reverse('checkout', args=[self.plan.pk]), {'amount_rial': 1, 'quote': quote})
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get()
        self.assertEqual(payment.amount_rial, 200000)
        payload = call.call_args.args[1]
        self.assertEqual(payload['amount'], 200000)
        self.assertEqual(payload['currency'], 'IRR')
        self.assertTrue(payload['callback_url'].startswith(settings.PUBLIC_BASE_URL))
        self.assertFalse(Entitlement.objects.exists())

    @patch.object(Zarinpal, 'verify', return_value='12345')
    def test_verified_payment_creates_one_grant_even_after_repeat(self, verify):
        payment = self.payment()
        result = verify_payment(payment)
        verify_payment(payment)  # Deliberately retry with stale pending object.
        self.assertEqual(result.status, 'paid')
        self.assertEqual(Entitlement.objects.count(), 1)
        self.assertTrue(can_browse(self.user))

    @patch.object(Zarinpal, 'verify', return_value='12346')
    def test_plan_edits_do_not_change_existing_purchase(self, verify):
        payment = self.payment()
        self.plan.duration_days = 1
        self.plan.save()
        result = verify_payment(payment)
        self.assertEqual(result.entitlement.ends_at - result.entitlement.starts_at, timedelta(days=30))

    @patch.object(Zarinpal, 'verify', side_effect=GatewayError('timeout'))
    def test_failed_verification_never_grants_access(self, verify):
        payment = self.payment()
        response = self.client.get(reverse('payment-callback', args=[payment.pk]), {'Authority': payment.authority, 'Status': 'OK'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Entitlement.objects.exists())
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')

    @patch.object(Zarinpal, 'verify', return_value='45678')
    def test_callback_does_not_require_session_but_detail_does(self, verify):
        payment = self.payment()
        self.client.logout()
        response = self.client.get(reverse('payment-callback', args=[payment.pk]), {'Authority': payment.authority, 'Status': 'OK'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entitlement.objects.count(), 1)
        self.assertEqual(self.client.get(reverse('payment-detail', args=[payment.pk])).status_code, 302)

    @patch.object(Zarinpal, 'verify')
    def test_forged_authority_and_cancelled_callback_do_not_verify(self, verify):
        payment = self.payment()
        path = reverse('payment-callback', args=[payment.pk])
        self.assertEqual(self.client.get(path, {'Authority': 'forged', 'Status': 'OK'}).status_code, 400)
        self.client.get(path, {'Authority': payment.authority, 'Status': 'NOK'})
        verify.assert_not_called()
        self.assertFalse(Entitlement.objects.exists())

    @patch.object(Zarinpal, 'verify', side_effect=['123', '124'])
    def test_same_plan_renewal_starts_after_existing_entitlement(self, verify):
        first = verify_payment(self.payment())
        second = verify_payment(self.payment(authority='S' + '2' * 35))
        self.assertEqual(second.entitlement.starts_at, first.entitlement.ends_at)

    @patch.object(Zarinpal, 'call', return_value={'code': 101, 'ref_id': 99})
    def test_already_verified_gateway_response_is_accepted(self, call):
        self.assertEqual(Zarinpal().verify(self.payment()), '99')

    @patch.object(Zarinpal, 'call', return_value={'code': -50})
    def test_gateway_negative_code_is_rejected(self, call):
        with self.assertRaises(GatewayError):
            Zarinpal().verify(self.payment())

    @patch.object(Zarinpal, 'verify', return_value='999')
    def test_storage_payment_does_not_grant_browse(self, verify):
        payment = self.payment(kind='storage', storage_mb=500)
        verify_payment(payment)
        self.assertEqual(storage_quota(self.user), 500 * MB)
        self.assertFalse(can_browse(self.user))

    @override_settings(ZARINPAL_MERCHANT_ID='')
    def test_checkout_disabled_without_merchant_credentials(self):
        response = self.client.post(reverse('checkout', args=[self.plan.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.exists())

    def test_other_account_cannot_read_payment(self):
        payment = self.payment()
        stranger = User.objects.create_user('stranger')
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(reverse('payment-detail', args=[payment.pk])).status_code, 404)

    @patch.object(Zarinpal, 'request')
    def test_price_change_requires_customer_to_confirm_again(self, gateway_request):
        path = reverse('checkout', args=[self.plan.pk])
        quote = self.client.get(path).context['quote']
        self.plan.price_rial = 500000
        self.plan.save()
        response = self.client.post(path, {'quote': quote})
        self.assertRedirects(response, path)
        gateway_request.assert_not_called()
        self.assertFalse(Payment.objects.exists())

    @patch.object(Zarinpal, 'request')
    def test_unsigned_checkout_request_does_not_create_order(self, gateway_request):
        self.client.post(reverse('checkout', args=[self.plan.pk]), {'quote': 'forged'})
        gateway_request.assert_not_called()
        self.assertFalse(Payment.objects.exists())

    @patch.object(Zarinpal, 'verify', return_value='888')
    def test_same_gateway_receipt_cannot_fulfill_two_orders(self, verify):
        verify_payment(self.payment())
        second = self.payment(authority='S' + '3' * 35)
        with self.assertRaises(IntegrityError), transaction.atomic():
            verify_payment(second)
        self.assertEqual(Entitlement.objects.count(), 1)

class BackupValidationTests(TestCase):
    def test_corrupted_backup_is_rejected(self):
        from .management.commands.backup_site import digest
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with closing(sqlite3.connect(root / 'db.sqlite3')) as db:
                db.execute('CREATE TABLE portfolio_portfoliofile (file TEXT, size INTEGER)')
                db.commit()
            manifest = {'version': 1, 'files': [{'path': 'db.sqlite3', 'sha256': digest(root / 'db.sqlite3')}]}
            (root / 'manifest.json').write_text(json.dumps(manifest))
            call_command('verify_backup', folder, stdout=io.StringIO())
            (root / 'db.sqlite3').write_bytes(b'corrupted')
            with self.assertRaises(CommandError):
                call_command('verify_backup', folder, stdout=io.StringIO())

    def test_existing_backup_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(CommandError):
                call_command('backup_site', folder)
