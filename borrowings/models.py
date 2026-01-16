from datetime import date
from typing import Type

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def validate_borrowing_dates(
    borrow_date: date,
    expected_return_date: date,
    actual_return_date: date | None,
    exc_to_raise: Type[Exception],
) -> None:
    for value, name in zip(
        (expected_return_date, actual_return_date),
        ("expected_return_date", "actual_return_date"),
    ):
        if value is not None and value <= borrow_date:
            raise exc_to_raise(
                {
                    name: f"This field value {value} cannot be the same"
                    f" or earlier than borrow_date {borrow_date}."
                }
            )


class Borrowing(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="borrowings"
    )
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="borrowings"
    )
    borrow_date = models.DateField(
        validators=[MinValueValidator(date.today)], default=date.today
    )
    expected_return_date = models.DateField(
        validators=[MinValueValidator(date.today)]
    )
    actual_return_date = models.DateField(
        validators=[MinValueValidator(date.today)], null=True, blank=True
    )

    def clean(self) -> None:
        validate_borrowing_dates(
            self.borrow_date,
            self.expected_return_date,
            self.actual_return_date,
            ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"User {self.user.id} borrowed {self.book} at {self.borrow_date}"
        )
