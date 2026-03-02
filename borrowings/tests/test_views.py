from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import stripe
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


@mock.patch("stripe.checkout.Session.create")
class TestViews(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()

    def setUp(self):
        self.book = Book.objects.create(
            title="TestBook",
            author="TestAuthor",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )
        self.user = get_user_model().objects.create_user(
            email="user@user.com", password="testuser123"
        )
        self.client.force_authenticate(self.user)
        self.test_stripe_session = stripe.checkout.Session()
        self.test_stripe_session.id = "test_id"
        self.test_stripe_session.url = "test_url"

    def test_create_borrowing(self, mock_stripe_create):
        mock_stripe_create.return_value = self.test_stripe_session
        url = reverse("borrowings:borrowing-list")
        response = self.client.post(
            url,
            data={
                "book": self.book.title,
                "borrow_date": date.today(),
                "expected_return_date": date.today() + timedelta(days=1),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)

    def test_search_active_borrowings(self, *args):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=1),
            expected_return_date=date.today(),
        )
        not_searched_book = Book.objects.create(
            title="NotActiveBorrowing",
            author="TestAuthor",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )
        Borrowing.objects.create(
            user=self.user,
            book=not_searched_book,
            borrow_date=date.today() - timedelta(days=1),
            expected_return_date=date.today(),
            actual_return_date=date.today(),
        )
        url = reverse("borrowings:borrowing-list")
        response = self.client.get(url, query_params={"is_active": "1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "TestBook")
        self.assertNotContains(response, "NotActiveBorrowing")

    def test_search_inactive_borrowings(self, *args):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=1),
            expected_return_date=date.today(),
        )
        searched_book = Book.objects.create(
            title="NotActiveBorrowing",
            author="TestAuthor",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )
        Borrowing.objects.create(
            user=self.user,
            book=searched_book,
            borrow_date=date.today() - timedelta(days=1),
            expected_return_date=date.today(),
            actual_return_date=date.today(),
        )
        url = reverse("borrowings:borrowing-list")
        response = self.client.get(url, query_params={"is_active": "0"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "NotActiveBorrowing")
        self.assertNotContains(response, "TestBook")

    def test_return_borrowing(self, *args):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=1),
            expected_return_date=date.today(),
        )
        url = reverse(
            "borrowings:borrowing-return", kwargs={"pk": borrowing.pk}
        )
        response = self.client.post(url)
        borrowing.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(borrowing.actual_return_date, date.today())

    def test_return_overdue_borrowing_creates_fine(self, mock_stripe_create):
        mock_stripe_create.return_value = self.test_stripe_session
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=3),
            expected_return_date=date.today() - timedelta(days=2),
        )
        url = reverse(
            "borrowings:borrowing-return", kwargs={"pk": borrowing.pk}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            Payment.objects.filter(type=Payment.PaymentType.FINE).first(),
            borrowing.payments.all(),
        )
