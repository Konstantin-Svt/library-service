from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
from notifications.tasks import send_borrowing_telegram


@receiver(post_save, sender=Borrowing)
def borrowing_created(sender, instance, created, **kwargs):
    if created:
        send_borrowing_telegram.delay_on_commit(instance.id)
