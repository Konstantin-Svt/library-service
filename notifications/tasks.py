from celery import shared_task

from borrowings.models import Borrowing
from notifications.telegram import send_telegram


@shared_task
def send_new_borrowing(borrowing_id: int) -> str:
    borrowing = Borrowing.objects.get(id=borrowing_id)
    text = (
        f"A new borrowing #{borrowing_id} of a book "
        f"'{borrowing.book.title}' has been "
        f"created at {borrowing.borrow_date}."
    )
    telegram_response = send_telegram(text)
    telegram_response.raise_for_status()

    return f"status={telegram_response.status_code}"
