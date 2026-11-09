from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import InvitationLink, PortfolioFile

@receiver(post_delete, sender=PortfolioFile)
def delete_private_blob(sender, instance, **kwargs):
    storage, name = instance.file.storage, instance.file.name
    transaction.on_commit(lambda: storage.delete(name))

@receiver(post_save, sender=get_user_model())
def create_invitation_link(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        InvitationLink.objects.get_or_create(user=instance)
