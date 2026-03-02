from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer


class TestSerializers(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )
        self.user = get_user_model().objects.create_user(
            email="TestMail", password="TestPassword"
        )

    def test_borrowing_list_serializer(self):
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=1),
        )
        serializer = BorrowingListSerializer(instance=borrowing)
        self.assertIn(borrowing.pk, serializer.data.values())
        self.assertIn(
            str(date.today() + timedelta(days=1)), serializer.data.values()
        )

    def test_borrowing_serializer_does_not_accept_payments_user_id(self):
        data = {
            "book": self.book,
            "user": self.user,
            "borrow_date": date.today(),
            "expected_return_date": date.today() + timedelta(days=1),
            "actual_return_date": date.today() + timedelta(days=2),
            "payments": [1, 2, 3],
        }
        serializer = BorrowingListSerializer(data=data)
        serializer.is_valid()

        self.assertNotIn("payments", serializer.data)
        self.assertNotIn(
            str(date.today() + timedelta(days=2)), serializer.data.values()
        )
        self.assertNotIn("payments", serializer.data)
        self.assertNotIn("user", serializer.data)
        self.assertIn("book", serializer.data)

    def test_borrowing_serializer_validates_incorrect_dates(self):
        data = {
            "book": self.book,
            "user": self.user,
            "borrow_date": date.today() - timedelta(days=2),
            "expected_return_date": date.today() - timedelta(days=1),
        }
        serializer = BorrowingListSerializer(data=data)
        self.assertFalse(serializer.is_valid())
