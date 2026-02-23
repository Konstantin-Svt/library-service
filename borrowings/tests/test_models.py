from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from books.models import Book
from borrowings.models import Borrowing


class BorrowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(
            email="TestMail", password="TestPassword"
        )
        cls.book = Book.objects.create(
            title="TestBook",
            author="TestAuthor",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )

    def test_actual_return_date_cant_be_earlier_than_borrow_date(self):
        today = date.today()
        borrowing = Borrowing(
            user=self.user,
            book=self.book,
            borrow_date=today + timedelta(days=1),
            expected_return_date=today + timedelta(days=2),
            actual_return_date=today,
        )
        self.assertRaises(ValidationError, borrowing.save)
        self.assertEqual(Borrowing.objects.count(), 0)

    def test_expected_return_date_cant_be_earlier_than_borrow_date(self):
        today = date.today()
        borrowing = Borrowing(
            user=self.user,
            book=self.book,
            borrow_date=today + timedelta(days=1),
            expected_return_date=today,
        )
        self.assertRaises(ValidationError, borrowing.save)
        self.assertEqual(Borrowing.objects.count(), 0)
