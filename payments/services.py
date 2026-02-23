from decimal import Decimal

import stripe
from django.conf import settings

from borrowings.models import Borrowing
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_payable_days(
    borrowing: Borrowing, payment_type: Payment.PaymentType
) -> int:
    if payment_type == Payment.PaymentType.PAYMENT:
        days = (borrowing.expected_return_date - borrowing.borrow_date).days
    else:
        days = (
            borrowing.actual_return_date - borrowing.expected_return_date
        ).days
    if days <= 0:
        raise ValueError("Payment days should be greater than 0")
    return days


def build_stripe_kwargs(
    title: str, payment_type: Payment.PaymentType, days: int, price: Decimal
) -> dict:
    extra = "" if payment_type == Payment.PaymentType.PAYMENT else " overdue"
    price_in_cents = int(price * 100)
    kwargs = {
        "line_items": [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{payment_type.label} for{extra} "
                        f"borrowing '{title}' "
                        f"for {days} day(s)",
                    },
                    "unit_amount": price_in_cents,
                },
                "quantity": 1,
            }
        ],
        "mode": "payment",
        "success_url": "https://stripe.com/checkout",
    }
    return kwargs


def create_stripe_payment(
    borrowing: Borrowing,
    payment_type: Payment.PaymentType = Payment.PaymentType.PAYMENT,
) -> Payment:
    days = calculate_payable_days(borrowing, payment_type)
    price = days * borrowing.book.daily_fee
    session = stripe.checkout.Session.create(
        **build_stripe_kwargs(borrowing.book.title, payment_type, days, price)
    )
    payment = Payment.objects.create(
        status=Payment.PaymentStatus.PENDING,
        type=payment_type,
        borrowing=borrowing,
        money_to_pay=price,
        session_id=session.id,
        session_url=session.url,
    )
    return payment
