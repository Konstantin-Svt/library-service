from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from requests import Response

from books.models import Book
from borrowings.models import Borrowing


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestSignals(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="TestMail", password="TestPassword"
        )
        self.book = Book.objects.create(
            title="TestBook",
            author="TestAuthor",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )

    @mock.patch("notifications.tasks.send_new_borrowing.delay_on_commit")
    def test_borrowing_created(self, mock_sending):
        mock_sending.return_value = "send"
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=1),
        )
        self.assertEqual(mock_sending.call_count, 1)
