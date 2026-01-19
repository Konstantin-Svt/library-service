import requests
from django.conf import settings
from celery import shared_task

from borrowings.models import Borrowing


@shared_task
def send_borrowing_telegram(borrowing_id: int) -> str:
    borrowing = Borrowing.objects.get(id=borrowing_id)
    text = (
        f"A new borrowing #{borrowing_id} of a book "
        f"'{borrowing.book.title}' has been "
        f"created at {borrowing.borrow_date}."
    )
    response = requests.post(
        url=f"https://api.telegram.org/bot{
            settings.TELEGRAM_BOT_TOKEN
        }/sendMessage",
        json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
        },
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    response.raise_for_status()

    return f"status={response.status_code}"
