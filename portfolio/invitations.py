from django.db import transaction
from django.utils import timezone
from .models import Invitation, InvitationLink, Profile


class InvitationUnavailable(Exception):
    pass


def register_invited_user(form, token):
    with transaction.atomic():
        updated = InvitationLink.objects.filter(token=token, is_active=True).update(last_used_at=timezone.now())
        if updated != 1:
            raise InvitationUnavailable

        link = InvitationLink.objects.select_related('user').get(token=token)
        user = form.save()
        Profile.objects.create(user=user, display_name=user.username)
        Invitation.objects.create(inviter=link.user, invitee=user, link=link)
    return user
