import base64
import binascii
import io
import json
import sqlite3
import struct
import tempfile
import threading
import zlib
import re
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core import mail
from django.db import IntegrityError, close_old_connections, transaction
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .access import can_browse, storage_quota, storage_used
from .billing import start_payment, verify_payment
from .forms import UploadForm
from .gateway import GatewayError, Zarinpal
from .models import MB, Entitlement, Favorite, Invitation, InvitationLink, Payment, Plan, PortfolioFile, Profile, RequestThrottle, SiteSettings, SupportRequest, WorkLink
from .security import rate_limit
from .media_validation import MediaDecoderUnavailable
from .services import add_file

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg==')


def mp4_box(kind, payload=b''):
    return struct.pack('>I', len(payload) + 8) + kind + payload


def png_chunk(kind, payload):
    chunk = kind + payload
    return struct.pack('>I', len(payload)) + chunk + struct.pack('>I', binascii.crc32(chunk) & 0xFFFFFFFF)


def padded_png(size):
    return (
        b'\x89PNG\r\n\x1a\n'
        + png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
        + png_chunk(b'tEXt', b'Comment\0' + b'x' * size)
        + png_chunk(b'IDAT', zlib.compress(b'\0\xff\0\0\xff'))
        + png_chunk(b'IEND', b'')
    )

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
        values = {
            'user': user or self.viewer,
            'kind': kind,
            'reference': 'test',
            'ends_at': timezone.now() + timedelta(days=1),
        }
        values.update(kwargs)
        return Entitlement.objects.create(**values)

    def upload(self, user=None, payload=PNG, filename='work.png'):
        self.client.force_login(user or self.owner)
        return self.client.post(reverse('upload'), {
            'title': 'تصویر تست', 'file': SimpleUploadedFile(filename, payload, 'application/octet-stream'),
        })

    def test_invited_signup_creates_one_profile_and_one_immutable_relation_without_rewards(self):
        response = self.client.post(reverse('signup-invitation', args=[self.owner.invitation_link.token]), {
            'username': 'new-artist', 'email': 'artist@example.test',
            'password1': 'Fresh-artist-password!', 'password2': 'Fresh-artist-password!',
        })
        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(username='new-artist')
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertFalse(user.profile.published)
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
        self.assertContains(self.client.get(reverse('directory'), {'q': 'هیچ‌کس'}), 'رزومه‌ای پیدا نشد')
        self.assertContains(self.client.get(reverse('profile', args=[self.artist.pk])), self.artist.display_name)
        self.assertEqual(self.client.post(reverse('favorite', args=[self.artist.pk])).status_code, 302)
        self.assertEqual(Favorite.objects.filter(user=self.viewer, profile=self.artist).count(), 1)
        self.assertEqual(self.client.post(reverse('favorite', args=[self.artist.pk])).status_code, 302)
        self.assertFalse(Favorite.objects.filter(user=self.viewer, profile=self.artist).exists())
        self.client.post(reverse('favorite', args=[self.artist.pk]))
        other_viewer = User.objects.create_user('other-viewer')
        self.grant(user=other_viewer)
        other_client = Client()
        other_client.force_login(other_viewer)
        self.assertEqual(other_client.post(reverse('favorite', args=[self.artist.pk])).status_code, 302)
        self.assertEqual(Favorite.objects.filter(profile=self.artist).count(), 2)
        self.client.post(reverse('favorite', args=[self.artist.pk]))
        self.assertEqual(Favorite.objects.filter(profile=self.artist).count(), 1)
        self.assertTrue(Favorite.objects.filter(user=other_viewer, profile=self.artist).exists())
        self.client.post(reverse('favorite', args=[self.artist.pk]))
        self.assertEqual(Favorite.objects.filter(profile=self.artist).count(), 2)
        self.assertContains(self.client.get(reverse('directory'), {'favorites': '1'}), self.artist.display_name)
        self.artist.published = False
        self.artist.save(update_fields=['published'])
        self.assertNotContains(self.client.get(reverse('directory'), {'favorites': '1'}), self.artist.display_name)
        self.assertEqual(self.client.get(reverse('profile', args=[self.artist.pk])).status_code, 403)
        expired_at = timezone.now() - timedelta(seconds=1)
        Entitlement.objects.filter(user=self.viewer).update(
            starts_at=expired_at - timedelta(days=1),
            ends_at=expired_at,
        )
        self.assertEqual(self.client.get(reverse('directory'), {'favorites': '1'}).status_code, 403)

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

    def test_profile_edit_validates_saves_and_escapes_private_content(self):
        self.owner.email = 'private-account@example.test'
        self.owner.save(update_fields=['email'])
        self.client.force_login(self.owner)
        response = self.client.post(reverse('edit-profile'), {
            'display_name': 'هنرمند ویرایش‌شده',
            'city': 'شیراز',
            'specialty': 'بازیگری',
            'skills': 'بیان، حرکت',
            'biography': "<script>document.body.dataset.synthetic='executed'</script>",
            'experience': 'اجرای آزمایشی',
            'contact': 'studio@example.test',
            'published': 'on',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.artist.refresh_from_db()
        self.assertEqual(self.artist.display_name, 'هنرمند ویرایش‌شده')
        self.assertEqual(self.artist.city, 'شیراز')
        self.assertEqual(self.artist.specialty, 'بازیگری')
        self.assertEqual(self.artist.skills, 'بیان، حرکت')
        self.assertEqual(
            self.artist.biography,
            "<script>document.body.dataset.synthetic='executed'</script>",
        )
        self.assertEqual(self.artist.experience, 'اجرای آزمایشی')
        self.assertEqual(self.artist.contact, 'studio@example.test')
        self.assertTrue(self.artist.published)

        profile_path = reverse('profile', args=[self.artist.pk])
        response = self.client.get(profile_path)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, "<script>document.body.dataset.synthetic='executed'</script>")
        self.assertContains(response, 'studio@example.test')
        self.assertNotContains(response, 'private-account@example.test')

        response = self.client.post(reverse('edit-profile'), {
            'display_name': '',
            'city': 'شیراز',
            'specialty': 'بازیگری',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['display_name'])
        self.artist.refresh_from_db()
        self.assertEqual(self.artist.display_name, 'هنرمند ویرایش‌شده')
        self.assertTrue(self.artist.published)

    def test_profile_and_private_file_access_matrix(self):
        self.upload()
        item = PortfolioFile.objects.get()
        profile_path = reverse('profile', args=[self.artist.pk])
        file_path = reverse('media', args=[item.pk])

        self.client.logout()
        self.assertEqual(self.client.get(profile_path).status_code, 302)
        self.assertEqual(self.client.get(file_path).status_code, 302)

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(profile_path).status_code, 200)
        owner_file = self.client.get(file_path)
        self.assertEqual(owner_file.status_code, 200)
        owner_file.close()

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(profile_path).status_code, 403)
        self.assertEqual(self.client.get(file_path).status_code, 403)
        self.assertEqual(self.client.get(reverse('directory')).status_code, 403)

        self.grant(kind='storage', storage_mb=500)
        self.assertEqual(storage_quota(self.viewer), 500 * MB)
        self.assertEqual(self.client.get(profile_path).status_code, 403)
        self.assertEqual(self.client.get(file_path).status_code, 403)
        self.assertEqual(self.client.get(reverse('directory')).status_code, 403)

        self.grant(kind='browse')
        self.assertEqual(storage_quota(self.viewer), 500 * MB)
        self.assertEqual(self.client.get(profile_path).status_code, 200)
        viewer_file = self.client.get(file_path)
        self.assertEqual(viewer_file.status_code, 200)
        viewer_file.close()
        self.assertEqual(self.client.get(reverse('directory')).status_code, 200)

    def test_profile_and_file_urls_recheck_expired_revoked_and_future_access(self):
        self.upload()
        item = PortfolioFile.objects.get()
        profile_path = reverse('profile', args=[self.artist.pk])
        file_path = reverse('media', args=[item.pk])
        now = timezone.now()
        grant = self.grant(
            starts_at=now - timedelta(seconds=1),
            ends_at=now + timedelta(seconds=30),
        )
        self.client.force_login(self.viewer)

        with patch('portfolio.access.timezone.now', return_value=now):
            self.assertEqual(self.client.get(profile_path).status_code, 200)
            response = self.client.get(file_path)
            self.assertEqual(response.status_code, 200)
            response.close()

        denied_states = [
            ({'ends_at': now}, now),
            ({'ends_at': now + timedelta(hours=1), 'revoked': True}, now),
            ({
                'starts_at': now + timedelta(seconds=1),
                'ends_at': now + timedelta(hours=1),
                'revoked': False,
            }, now),
        ]
        for updates, checked_at in denied_states:
            Entitlement.objects.filter(pk=grant.pk).update(**updates)
            with patch('portfolio.access.timezone.now', return_value=checked_at):
                self.assertEqual(self.client.get(profile_path).status_code, 403)
                self.assertEqual(self.client.get(file_path).status_code, 403)

        self.assertTrue(Path(item.file.path).is_file())
        self.assertTrue(PortfolioFile.objects.filter(pk=item.pk).exists())
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(profile_path).status_code, 200)
        owner_file = self.client.get(file_path)
        self.assertEqual(owner_file.status_code, 200)
        owner_file.close()

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
        self.assertEqual(self.client.get('/media/' + item.file.name).status_code, 404)
        dashboard = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard.context['quota_mb'], 100)
        self.assertEqual(dashboard.context['used_mb'], len(PNG) / MB)

    def test_complete_png_is_accepted_and_extension_mismatch_is_rejected(self):
        form = UploadForm(
            {'title': 'synthetic'},
            {'file': SimpleUploadedFile('sample.png', PNG, 'application/octet-stream')},
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['file'].detected_content_type, 'image/png')

        invalid = UploadForm(
            {'title': 'synthetic'},
            {'file': SimpleUploadedFile('sample.jpg', PNG, 'image/jpeg')},
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn('file', invalid.errors)

    def test_external_work_links_do_not_consume_storage(self):
        WorkLink.objects.create(profile=self.artist, title='نمونه ساختگی', url='https://example.test/work')
        self.assertEqual(storage_used(self.artist), 0)

    def test_rejects_truncated_and_malformed_media_without_saving(self):
        malformed_png = bytearray(PNG)
        malformed_png[29] ^= 0x01
        malformed_webp = (
            b'RIFF' + struct.pack('<I', 22) + b'WEBPVP8 ' + struct.pack('<I', 10)
            + bytes.fromhex('0000009d012a01000100')
        )
        empty_tables = b''.join(
            mp4_box(tag) for tag in (b'stsd', b'stts', b'stsc', b'stsz', b'stco')
        )
        malformed_mp4 = (
            mp4_box(b'ftyp', b'isom\0\0\0\0')
            + mp4_box(b'mdat', b'not-video')
            + mp4_box(
                b'moov',
                mp4_box(
                    b'trak',
                    mp4_box(
                        b'mdia',
                        mp4_box(b'hdlr', b'\0' * 8 + b'vide')
                        + mp4_box(b'minf', mp4_box(b'stbl', empty_tables)),
                    ),
                ),
            )
        )
        invalid_files = (
            ('work.png', PNG[:8]),
            ('work.png', PNG[:-5]),
            ('work.png', PNG + b'extra bytes after IEND'),
            ('work.png', bytes(malformed_png)),
            ('work.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 24),
            ('work.jpg', b'\xff\xd8\xff'),
            ('work.webp', b'RIFF\x00\x00\x00\x00WEBP'),
            ('work.webp', malformed_webp),
            ('work.mp4', b'\x00\x00\x00\x18ftyp'),
            ('work.mp4', malformed_mp4),
            ('work.webm', b'\x1aE\xdf\xa3\x9f'),
        )
        for filename, payload in invalid_files:
            with self.subTest(filename=filename, payload_length=len(payload)):
                response = self.upload(payload=payload, filename=filename)
                self.assertContains(response, 'فایل معتبر')
                self.assertFalse(PortfolioFile.objects.exists())
                self.assertEqual(storage_used(self.artist), 0)
                self.assertEqual(list(Path(self.media.name).rglob('*.*')), [])

    def test_missing_image_decoder_has_an_explicit_configuration_error(self):
        uploaded = SimpleUploadedFile('sample.png', PNG, 'image/png')
        with patch.dict('sys.modules', {'PIL': None}):
            with self.assertRaisesRegex(MediaDecoderUnavailable, 'Pillow is required'):
                UploadForm({'title': 'synthetic'}, {'file': uploaded}).is_valid()

    def test_external_work_link_can_be_added_and_removed_without_storage_use(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('add-link'), {
            'title': 'اثر پیوندی ساختگی',
            'url': 'https://example.test/synthetic-work',
        })
        self.assertEqual(response.status_code, 302)
        link = WorkLink.objects.get(profile=self.artist)
        self.assertContains(self.client.get(reverse('dashboard')), 'اثر پیوندی ساختگی')
        self.assertContains(self.client.get(reverse('profile', args=[self.artist.pk])), 'اثر پیوندی ساختگی')
        self.assertEqual(storage_used(self.artist), 0)

        response = self.client.post(reverse('delete-link', args=[link.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WorkLink.objects.filter(pk=link.pk).exists())
        self.assertEqual(storage_used(self.artist), 0)

    def test_media_audit_reports_missing_untracked_and_size_mismatch_without_deleting(self):
        self.upload()
        missing_record = PortfolioFile.objects.order_by('created_at').first()
        missing_path = Path(missing_record.file.path)
        self.upload()
        mismatched_record = PortfolioFile.objects.exclude(pk=missing_record.pk).first()
        self.upload()
        intact_record = PortfolioFile.objects.exclude(
            pk__in=[missing_record.pk, mismatched_record.pk],
        ).get()
        PortfolioFile.objects.filter(pk=mismatched_record.pk).update(size=len(PNG) + 1)
        missing_path.unlink()
        orphan_path = Path(self.media.name) / 'untracked-synthetic.bin'
        orphan_path.write_bytes(b'synthetic orphan')

        output = io.StringIO()
        with self.assertRaises(CommandError):
            call_command('audit_portfolio_media', stdout=output)
        report = output.getvalue()
        self.assertIn('1 missing, 1 untracked, 1 size mismatch(es)', report)
        self.assertIn(f'MISSING record={missing_record.pk}', report)
        self.assertIn('UNTRACKED name=untracked-synthetic.bin', report)
        self.assertIn(f'SIZE_MISMATCH record={mismatched_record.pk}', report)
        self.assertFalse(missing_path.exists())
        self.assertTrue(orphan_path.is_file())
        self.assertTrue(Path(intact_record.file.path).is_file())
        self.assertEqual(PortfolioFile.objects.count(), 3)
        self.assertEqual(PortfolioFile.objects.get(pk=mismatched_record.pk).size, len(PNG) + 1)

    def test_media_audit_reports_clean_store_without_changes(self):
        self.upload()
        output = io.StringIO()
        call_command('audit_portfolio_media', stdout=output)
        self.assertIn('No discrepancies found; no data was changed.', output.getvalue())

    def test_media_audit_handles_an_uncreated_empty_storage_root(self):
        Path(self.media.name).rmdir()
        output = io.StringIO()
        call_command('audit_portfolio_media', stdout=output)
        self.assertIn('0 database records, 0 stored files, 0 missing', output.getvalue())

    def test_reject_upload_when_quota_full_without_saving_file(self):
        SiteSettings.objects.filter(pk=1).update(free_storage_mb=0)
        response = self.upload()
        self.assertContains(response, 'فضای کافی ندارید')
        self.assertFalse(PortfolioFile.objects.exists())
        self.assertEqual(list(Path(self.media.name).rglob('*.png')), [])

    def test_reject_next_upload_when_combined_size_exceeds_quota(self):
        SiteSettings.objects.filter(pk=1).update(free_storage_mb=1)
        payload = padded_png(600_000)
        self.assertEqual(self.upload(payload=payload).status_code, 302)
        self.assertContains(self.upload(payload=payload), 'فضای کافی ندارید')
        self.assertEqual(PortfolioFile.objects.count(), 1)

    @override_settings(MAX_UPLOAD_BYTES=32)
    def test_streaming_limit_rejects_large_upload(self):
        self.assertContains(self.upload(), 'حجم فایل از سقف مجاز')
        self.assertFalse(PortfolioFile.objects.exists())
        self.assertEqual(list(Path(self.media.name).rglob('*.*')), [])

    def test_fake_image_and_html_rejected(self):
        response = self.upload(payload=b'<html>not an image</html>')
        self.assertContains(response, 'فایل معتبر')
        self.assertFalse(PortfolioFile.objects.exists())
        self.assertEqual(list(Path(self.media.name).rglob('*.*')), [])

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

    def test_storage_entitlement_expiry_keeps_existing_files_and_blocks_new_ones(self):
        SiteSettings.objects.filter(pk=1).update(free_storage_mb=0)
        now = timezone.now()
        grant = self.grant(
            user=self.owner,
            kind='storage',
            storage_mb=1,
            starts_at=now - timedelta(days=2),
            ends_at=now + timedelta(days=1),
        )
        self.assertEqual(self.upload().status_code, 302)
        item = PortfolioFile.objects.get()
        path = Path(item.file.path)
        Entitlement.objects.filter(pk=grant.pk).update(
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(seconds=1),
        )
        self.assertEqual(storage_quota(self.owner), 0)
        response = self.client.get(reverse('media', args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertContains(self.upload(), 'فضای کافی ندارید')
        self.assertTrue(path.is_file())
        self.assertTrue(PortfolioFile.objects.filter(pk=item.pk).exists())
        self.assertEqual(PortfolioFile.objects.count(), 1)

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
        self.assertEqual(payment.status, Payment.Status.UNKNOWN)

    @patch.object(Zarinpal, 'verify', return_value='45678')
    def test_callback_does_not_require_session_but_detail_does(self, verify):
        payment = self.payment()
        self.client.logout()
        response = self.client.get(reverse('payment-callback', args=[payment.pk]), {'Authority': payment.authority, 'Status': 'OK'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entitlement.objects.count(), 1)
        self.assertEqual(self.client.get(reverse('payment-detail', args=[payment.pk])).status_code, 302)

    @patch.object(Zarinpal, 'verify', return_value='98760')
    def test_forged_authority_and_nok_callback_remain_recoverable(self, verify):
        payment = self.payment()
        path = reverse('payment-callback', args=[payment.pk])
        self.assertEqual(self.client.get(path, {'Authority': 'forged', 'Status': 'OK'}).status_code, 400)
        self.client.get(path, {'Authority': payment.authority, 'Status': 'NOK'})
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.UNKNOWN)
        self.client.get(path, {'Authority': payment.authority, 'Status': 'OK'})
        verify.assert_called_once()
        self.assertEqual(Entitlement.objects.count(), 1)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)

    @patch.object(Zarinpal, 'verify', return_value='98761')
    def test_late_nok_never_downgrades_paid_payment(self, verify):
        payment = self.payment()
        path = reverse('payment-callback', args=[payment.pk])
        self.client.get(path, {'Authority': payment.authority, 'Status': 'OK'})
        self.client.get(path, {'Authority': payment.authority, 'Status': 'NOK'})
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(Entitlement.objects.count(), 1)

    @patch.object(Zarinpal, 'verify', side_effect=GatewayError('timeout'))
    def test_success_callback_timeout_marks_payment_unknown_without_grant(self, verify):
        payment = self.payment()
        response = self.client.get(
            reverse('payment-callback', args=[payment.pk]),
            {'Authority': payment.authority, 'Status': 'OK'},
        )
        self.assertRedirects(response, reverse('payment-detail', args=[payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.UNKNOWN)
        self.assertFalse(Entitlement.objects.exists())
        verify.assert_called_once()

    @patch.object(Zarinpal, 'verify', return_value='98765')
    def test_reconcile_command_lists_and_verifies_unresolved_orders(self, verify):
        payment = self.payment()
        payment.status = Payment.Status.UNKNOWN
        payment.save(update_fields=['status'])
        output = io.StringIO()
        call_command('reconcile_payments', stdout=output)
        self.assertIn(str(payment.pk), output.getvalue())
        self.assertEqual(Entitlement.objects.count(), 0)
        call_command('reconcile_payments', '--verify', stdout=output)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(Entitlement.objects.count(), 1)
        verify.assert_called_once()

    def test_canceled_payment_with_authority_can_be_recovered(self):
        payment = self.payment(status=Payment.Status.CANCELED)
        with patch.object(Zarinpal, 'verify', return_value='98762') as verify:
            verify_payment(payment)
        verify.assert_called_once()
        self.assertEqual(Payment.objects.get(pk=payment.pk).status, Payment.Status.PAID)

    def test_failed_without_authority_has_no_retry_action(self):
        payment = self.payment(status=Payment.Status.FAILED, authority=None)
        response = self.client.get(reverse('payment-detail', args=[payment.pk]))
        self.assertContains(response, 'درخواست پرداخت ناموفق بود')
        self.assertNotContains(response, reverse('payment-retry', args=[payment.pk]))

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


@override_settings(ZARINPAL_MERCHANT_ID='00000000-0000-0000-0000-000000000000', ZARINPAL_SANDBOX=True)
class PaymentConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user('concurrent-payer', password='Strong-password!')
        Profile.objects.create(user=self.user, display_name='concurrent-payer')
        self.plan = Plan.objects.create(
            name='مشاهده هم‌زمان', kind='browse', price_rial=200000, duration_days=30,
        )
        self.payment = Payment.objects.create(
            user=self.user, plan=self.plan, plan_name=self.plan.name, kind='browse',
            duration_days=30, amount_rial=200000, authority='S' + '9' * 35,
        )

    @patch.object(Zarinpal, 'verify', return_value='54321')
    def test_callback_retry_and_reconciliation_contention_grants_once(self, verify):
        barrier = threading.Barrier(3)
        errors = []

        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                verify_payment(Payment.objects.get(pk=self.payment.pk))
            except Exception as error:
                errors.append(error)
            finally:
                close_old_connections()

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(Entitlement.objects.count(), 1)
        self.assertEqual(Payment.objects.filter(ref_id='54321').count(), 1)
        self.assertGreaterEqual(verify.call_count, 1)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    LOGIN_RATE_LIMIT=2,
    LOGIN_RATE_WINDOW=3600,
    SIGNUP_RATE_LIMIT=1,
    SIGNUP_RATE_WINDOW=3600,
    CHECKOUT_RATE_LIMIT=1,
    CHECKOUT_RATE_WINDOW=3600,
    UPLOAD_RATE_LIMIT=1,
    UPLOAD_RATE_WINDOW=3600,
)
class AccountSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'security-user', 'security@example.test', 'Old-strong-password!2',
        )
        Profile.objects.create(user=self.user, display_name='Security user')
        self.plan = Plan.objects.create(
            name='امنیت', kind='browse', price_rial=200000, duration_days=30,
        )

    def test_password_reset_is_generic_single_use_and_invalid_after_password_change(self):
        response = self.client.post(reverse('password_reset'), {'email': 'nobody@example.test'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)
        self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        match = re.search(r'/reset/([^/]+)/([^/\s]+)/', body)
        self.assertIsNotNone(match)
        reset_url = reverse(
            'password_reset_confirm',
            kwargs={'uidb64': match.group(1), 'token': match.group(2)},
        )
        response = self.client.get(reset_url, follow=True)
        self.assertContains(response, 'رمز عبور جدید')
        response = self.client.post(response.request['PATH_INFO'], {
            'new_password1': 'New-strong-password!3',
            'new_password2': 'New-strong-password!3',
        })
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.assertEqual(self.client.get(reset_url).status_code, 200)
        self.assertContains(self.client.get(reset_url), 'پیوند معتبر نیست')
        self.assertTrue(self.client.login(username='security-user', password='New-strong-password!3'))

    def test_login_limit_is_persistent_and_does_not_use_forwarded_ip(self):
        for _ in range(2):
            response = self.client.post(reverse('login'), {
                'username': 'security-user', 'password': 'wrong',
                'HTTP_X_FORWARDED_FOR': '10.0.0.1',
            })
            self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('login'), {
            'username': 'security-user', 'password': 'Old-strong-password!2',
            'HTTP_X_FORWARDED_FOR': '10.0.0.2',
        })
        self.assertEqual(response.status_code, 429)

    @override_settings(
        LOGIN_RATE_LIMIT=1, SIGNUP_RATE_LIMIT=1, UPLOAD_RATE_LIMIT=1,
        SUPPORT_RATE_LIMIT=1, LOGIN_RATE_WINDOW=3600,
    )
    def test_empty_and_malformed_forms_return_429_with_retry_after(self):
        invitation = self.user.invitation_link
        cases = [
            (reverse('login'), {}, 'تلاش‌های ورود'),
            (reverse('signup-invitation', args=[invitation.token]), {}, 'تلاش‌های ثبت‌نام'),
            (reverse('upload'), {}, 'بارگذاری‌های اخیر'),
            (reverse('support'), {}, 'درخواست‌های اخیر'),
        ]
        for path, data, message in cases:
            RequestThrottle.objects.all().delete()
            if path in {reverse('upload'), reverse('support')}:
                self.client.force_login(self.user)
            else:
                self.client.logout()
            first = self.client.post(path, data)
            self.assertEqual(first.status_code, 200)
            second = self.client.post(path, data)
            self.assertEqual(second.status_code, 429)
            self.assertTrue(second.headers.get('Retry-After'))
            self.assertIn(message, second.content.decode())

    @override_settings(LOGIN_RATE_LIMIT=1, LOGIN_RATE_WINDOW=3600)
    def test_admin_login_shares_login_limit_with_normal_login(self):
        RequestThrottle.objects.all().delete()
        self.assertEqual(
            self.client.post(reverse('login'), {
                'username': 'security-user', 'password': 'wrong',
            }).status_code,
            200,
        )
        response = self.client.post('/admin/login/', {
            'username': 'security-user', 'password': 'wrong',
        })
        self.assertEqual(response.status_code, 429)
        self.assertTrue(response.headers.get('Retry-After'))
        self.assertIn('تلاش‌های ورود', response.content.decode())

    @override_settings(PASSWORD_RESET_RATE_LIMIT=2, PASSWORD_RESET_RATE_WINDOW=3600)
    def test_password_reset_limit_is_generic_and_stops_repeated_mail(self):
        RequestThrottle.objects.all().delete()
        first = self.client.post(reverse('password_reset'), {'email': 'nobody@example.test'})
        second = self.client.post(reverse('password_reset'), {'email': self.user.email})
        third = self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertRedirects(first, reverse('password_reset_done'))
        self.assertRedirects(second, reverse('password_reset_done'))
        self.assertEqual(third.status_code, 429)
        self.assertTrue(third.headers.get('Retry-After'))
        self.assertEqual(len(mail.outbox), 1)

    def test_non_staff_cannot_enter_admin_and_staff_without_permission_cannot_manage(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        response = self.client.get('/admin/', follow=True)
        self.assertNotContains(response, 'افزودن')
        self.assertEqual(self.client.get('/admin/portfolio/payment/add/').status_code, 403)

    def test_staff_permission_matrix_is_model_scoped(self):
        self.user.is_staff = True
        permissions = [
            ('auth', 'user'),
            ('portfolio', 'invitationlink'),
            ('portfolio', 'invitation'),
            ('portfolio', 'profile'),
            ('portfolio', 'plan'),
            ('portfolio', 'entitlement'),
            ('portfolio', 'payment'),
            ('portfolio', 'supportrequest'),
        ]
        for app_label, model in permissions:
            self.user.user_permissions.add(
                Permission.objects.get(
                    codename=f'view_{model}', content_type__app_label=app_label,
                ),
            )
        self.user.save(update_fields=['is_staff'])
        self.client.force_login(self.user)
        paths = [
            '/admin/auth/user/',
            '/admin/portfolio/invitationlink/',
            '/admin/portfolio/invitation/',
            '/admin/portfolio/profile/',
            '/admin/portfolio/plan/',
            '/admin/portfolio/entitlement/',
            '/admin/portfolio/payment/',
            '/admin/portfolio/supportrequest/',
        ]
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.user.user_permissions.remove(
            Permission.objects.get(codename='view_payment', content_type__app_label='portfolio'),
        )
        self.assertEqual(self.client.get('/admin/portfolio/payment/').status_code, 403)

    def test_support_and_account_deletion_are_requests_not_automatic_deletion(self):
        self.client.force_login(self.user)
        for page in ('terms', 'privacy', 'content-rules'):
            self.assertContains(self.client.get(reverse('legal', args=[page])), 'پیش‌نویس')
        self.assertContains(self.client.get(reverse('support')), 'درخواست پشتیبانی')
        self.assertContains(self.client.get(reverse('report-content')), 'گزارش محتوا')
        response = self.client.post(reverse('account-deletion'), {
            'subject': 'حذف حساب', 'message': 'لطفاً درخواست را بررسی کنید.',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(SupportRequest.objects.get().kind, SupportRequest.Kind.ACCOUNT)

    def test_failed_checkout_is_rate_limited_without_affecting_callback(self):
        self.client.force_login(self.user)
        quote = self.client.get(reverse('checkout', args=[self.plan.pk])).context['quote']
        self.assertEqual(self.client.post(reverse('checkout', args=[self.plan.pk]), {'quote': quote}).status_code, 302)
        response = self.client.post(reverse('checkout', args=[self.plan.pk]), {'quote': quote})
        self.assertEqual(response.status_code, 429)

    def test_signup_and_upload_limits_are_applied_to_invalid_and_valid_attempts(self):
        invitation = self.user.invitation_link
        signup_data = {
            'username': 'new-security-user', 'email': 'new@example.test',
            'password1': 'New-strong-password!3', 'password2': 'mismatch',
        }
        self.assertEqual(
            self.client.post(reverse('signup-invitation', args=[invitation.token]), signup_data).status_code,
            200,
        )
        signup_data['password2'] = signup_data['password1']
        self.assertEqual(
            self.client.post(reverse('signup-invitation', args=[invitation.token]), signup_data).status_code,
            429,
        )
        self.client.force_login(self.user)
        upload_data = {'title': 'نمونه', 'file': SimpleUploadedFile('sample.png', PNG, 'image/png')}
        self.assertEqual(self.client.post(reverse('upload'), upload_data).status_code, 302)
        upload_data = {'title': 'نمونه دوم', 'file': SimpleUploadedFile('sample2.png', PNG, 'image/png')}
        self.assertEqual(self.client.post(reverse('upload'), upload_data).status_code, 429)


@override_settings(LOGIN_RATE_LIMIT=5, LOGIN_RATE_WINDOW=3600)
class RateLimitConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def test_sqlite_workers_do_not_exceed_shared_quota(self):
        factory = RequestFactory()
        barrier = threading.Barrier(10)
        results, errors = [], []
        lock = threading.Lock()

        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                request = factory.post('/login/', {}, REMOTE_ADDR='192.0.2.10')
                allowed, _ = rate_limit(request, 'login')
                with lock:
                    results.append(allowed)
            except Exception as error:
                with lock:
                    errors.append(error)
            finally:
                close_old_connections()

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 10)
        self.assertGreaterEqual(sum(results), 1)
        self.assertLessEqual(sum(results), 5)
        self.assertEqual(RequestThrottle.objects.get().attempts, sum(results))

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
