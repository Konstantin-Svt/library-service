import hashlib
import hmac
import json
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock
from time import time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


class TestViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="testpass12345",
        )
        self.client.force_authenticate(self.user)
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.00"),
        )
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=1),
        )

    def test_payment_list_view(self):
        Payment.objects.create(
            borrowing=self.borrowing,
            status="PAID",
            type="PAYMENT",
            money_to_pay=Decimal("1.00"),
            session_url="test_url1234",
            session_id="test_id",
        )
        url = reverse("payments:payment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test_url1234")
        self.assertContains(response, "test_id")

    def test_other_user_payment_available_to_admin_only(self):
        other_user = get_user_model().objects.create_user(
            email="test222@test.com",
            password="testpass12345",
        )
        self.borrowing.user = other_user
        self.borrowing.save(update_fields=["user"])
        Payment.objects.create(
            borrowing=self.borrowing,
            status="PAID",
            type="PAYMENT",
            money_to_pay=Decimal("1.00"),
            session_url="test_url1234",
            session_id="test_id",
        )
        url = reverse("payments:payment-list")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test_url1234")

        self.user.is_staff = False
        self.user.save(update_fields=["is_staff"])

        response = self.client.get(url)
        self.assertNotContains(response, "test_url1234")

    def test_payment_success_view_requires_session_id(self):
        Payment.objects.create(
            borrowing=self.borrowing,
            status="PAID",
            type="PAYMENT",
            money_to_pay=Decimal("1.00"),
            session_url="test_url1234",
            session_id="test_id",
        )
        url = reverse("payments:payment-success")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        response = self.client.get(url, query_params={"session_id": "test_id"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paid")

    @override_settings(STRIPE_WEBHOOK_SECRET="super_secret1234")
    def test_stripe_webhook_accessible_by_stripe(self):
        payment = Payment.objects.create(
            borrowing=self.borrowing,
            status="PENDING",
            type="PAYMENT",
            money_to_pay=Decimal("1.00"),
            session_url="test_url1234",
            session_id="test_id",
        )
        payload_dict = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "test_id"}},
        }

        payload = json.dumps(payload_dict)
        timestamp = str(int(time()))
        signed_payload = f"{timestamp}.{payload}".encode()
        secret = "super_secret1234"
        signature = hmac.new(
            secret.encode(), signed_payload, hashlib.sha256
        ).hexdigest()
        sig_header = f"t={timestamp},v1={signature}"
        url = reverse("payments:stripe_webhook")
        response = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )
        payment.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, "PAID")

    @mock.patch("payments.views.mark_paid")
    @override_settings(STRIPE_WEBHOOK_SECRET="super_secret12345")
    def test_stripe_webhook_not_accessible_by_anyone(self, mocked_marking):
        payload_dict = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "test_id"}},
        }

        payload = json.dumps(payload_dict)
        timestamp = str(int(time()))
        signed_payload = f"{timestamp}.{payload}".encode()
        secret = "guess"
        signature = hmac.new(
            secret.encode(), signed_payload, hashlib.sha256
        ).hexdigest()
        sig_header = f"t={timestamp},v1={signature}"
        url = reverse("payments:stripe_webhook")
        response = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(mocked_marking.call_count, 0)
