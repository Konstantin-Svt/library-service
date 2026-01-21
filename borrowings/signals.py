from typing import Type

from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
from notifications.tasks import send_new_borrowing


@receiver(post_save, sender=Borrowing)
def borrowing_created(
    sender: Type[Borrowing], instance: Borrowing, created: bool, **kwargs
) -> None:
    if created:
        send_new_borrowing.delay_on_commit(instance.id)
