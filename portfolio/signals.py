from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import PortfolioFile

@receiver(post_delete, sender=PortfolioFile)
def delete_private_blob(sender, instance, **kwargs):
    storage, name = instance.file.storage, instance.file.name
    transaction.on_commit(lambda: storage.delete(name))
