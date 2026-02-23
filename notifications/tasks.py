from datetime import date

from celery import shared_task

from borrowings.models import Borrowing
from notifications.telegram import send_telegram


@shared_task(
    bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3}
)
def send_new_borrowing(self, borrowing_id: int) -> str:
    borrowing = Borrowing.objects.get(id=borrowing_id)
    text = (
        f"A new borrowing #{borrowing_id} of a book "
        f"'{borrowing.book.title}' has been "
        f"created at {borrowing.borrow_date} "
        f"with expected return date "
        f"of {borrowing.expected_return_date} by "
        f"user #{borrowing.user.id} {borrowing.user.email}."
    )
    telegram_response = send_telegram(text)
    telegram_response.raise_for_status()

    return f"borrowing={borrowing_id}, status={telegram_response.status_code}"


@shared_task(
    bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3}
)
def send_overdue_borrowings(self) -> str:
    borrowings = list(
        Borrowing.objects.filter(
            actual_return_date=None, expected_return_date__lte=date.today()
        )
        .select_related("book", "user")
    )

    if not borrowings:
        telegram_response = send_telegram("No borrowings overdue today!")
        telegram_response.raise_for_status()
        return f"No overdue, status={telegram_response.status_code}"

    counter = 0
    for borrowing in borrowings:
        text = (
            f"The borrowing #{borrowing.id} of a book "
            f"'{borrowing.book.title}' is overdue."
            f"Expected return date was "
            f"{borrowing.expected_return_date} by user"
            f"#{borrowing.user.id} {borrowing.user.email}."
        )
        telegram_response = send_telegram(text)
        telegram_response.raise_for_status()
        counter += 1

    return f"{counter} overdue borrowings sent successfully."
