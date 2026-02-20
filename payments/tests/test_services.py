from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.services import calculate_payable_days, calculate_price
from users.models import User


class TestServices(TestCase):
    def setUp(self):
        self.user = User(id=1)
        self.book = Book(title="test", author="test")

    def test_calculate_default_payable_days(self):
        testcases = [
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2020, 12, 15),
                expected_return_date=date(2020, 12, 31),
            ),
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2020, 11, 29),
                expected_return_date=date(2020, 11, 30),
            ),
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2021, 5, 8),
                expected_return_date=date(2021, 5, 20),
            ),
        ]
        results = [16, 1, 12]

        for testcase, result in zip(testcases, results):
            with self.subTest(testcase=testcase, result=result):
                count = calculate_payable_days(
                    borrowing=testcase,
                    payment_type=Payment.PaymentType.PAYMENT,
                )
                self.assertEqual(count, result)

    def test_calculate_fine_payable_days(self):
        testcases = [
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2020, 12, 15),
                expected_return_date=date(2020, 12, 16),
                actual_return_date=date(2020, 12, 31),
            ),
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2020, 11, 28),
                expected_return_date=date(2020, 11, 29),
                actual_return_date=date(2020, 11, 30),
            ),
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2021, 5, 8),
                expected_return_date=date(2021, 5, 20),
                actual_return_date=date(2021, 5, 25),
            ),
        ]
        results = [15, 1, 5]

        for testcase, result in zip(testcases, results):
            with self.subTest(testcase=testcase, result=result):
                count = calculate_payable_days(
                    borrowing=testcase,
                    payment_type=Payment.PaymentType.FINE,
                )
                self.assertEqual(count, result)

    def test_calculate_incorrect_payable_days(self):
        testcases = [
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2020, 12, 16),
                expected_return_date=date(2020, 12, 16),
            ),
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2020, 11, 28),
                expected_return_date=date(2020, 11, 11),
            ),
            Borrowing(
                user=self.user,
                book=self.book,
                borrow_date=date(2021, 5, 8),
                expected_return_date=date(2021, 5, 20),
                actual_return_date=date(2021, 5, 20),
            ),
        ]
        payment_types = [
            Payment.PaymentType.PAYMENT,
            Payment.PaymentType.PAYMENT,
            Payment.PaymentType.FINE,
        ]
        for testcase, payment_type in zip(testcases, payment_types):
            with self.subTest(testcase=testcase, payment_type=payment_type):
                self.assertRaises(
                    ValueError,
                    calculate_payable_days,
                    borrowing=testcase,
                    payment_type=payment_type,
                )

    def test_calculate_default_prices(self):
        daily_fees = [
            Decimal("1.00"),
            Decimal("0.01"),
            Decimal("0.00"),
            Decimal("2.33"),
        ]
        days = [5, 7, 1, 3]
        results = [
            Decimal("5.00"),
            Decimal("0.07"),
            Decimal("0.00"),
            Decimal("6.99"),
        ]

        for fee, day, result in zip(daily_fees, days, results):
            with self.subTest(fee=fee, day=day):
                count = calculate_price(
                    daily_fee=fee,
                    days=day,
                    payment_type=Payment.PaymentType.PAYMENT,
                )
                self.assertEqual(count, result)

    @override_settings(
        STRIPE_FINE_MULTIPLIER=3,
    )
    def test_calculate_fine_prices(self):
        daily_fees = [
            Decimal("1.00"),
            Decimal("0.01"),
            Decimal("0.00"),
            Decimal("2.33"),
        ]
        days = [5, 7, 1, 3]
        results = [
            Decimal("15.00"),
            Decimal("0.21"),
            Decimal("0.00"),
            Decimal("20.97"),
        ]

        for fee, day, result in zip(daily_fees, days, results):
            with self.subTest(fee=fee, day=day):
                count = calculate_price(
                    daily_fee=fee,
                    days=day,
                    payment_type=Payment.PaymentType.FINE,
                )
                self.assertEqual(count, result)
