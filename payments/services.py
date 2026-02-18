from decimal import Decimal

import stripe
from django.conf import settings
from django.http import HttpRequest
from rest_framework.reverse import reverse

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


def calculate_price(
    daily_fee: Decimal, days: int, payment_type: Payment.PaymentType
) -> Decimal:
    multiplier = 1
    if payment_type == Payment.PaymentType.FINE:
        multiplier = settings.STRIPE_FINE_MULTIPLIER
    return daily_fee * days * multiplier


def build_stripe_kwargs(
    request: HttpRequest,
    book_title: str,
    payment_type: Payment.PaymentType,
    days: int,
    price: Decimal,
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
                        f"borrowing '{book_title}' "
                        f"for {days} day(s)",
                    },
                    "unit_amount": price_in_cents,
                },
                "quantity": 1,
            }
        ],
        "mode": "payment",
        "success_url": f"{reverse(
            'payments:payment-success', request=request
        )}"
        + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": f"{reverse('payments:payment-cancel', request=request)}"
        + "?session_id={CHECKOUT_SESSION_ID}",
    }
    return kwargs


def create_stripe_payment(
    request: HttpRequest,
    borrowing: Borrowing,
    payment_type: Payment.PaymentType = Payment.PaymentType.PAYMENT,
) -> Payment:
    """
    Accepts request as first parameter
    to create success & cancel urls.
    """
    days = calculate_payable_days(borrowing, payment_type)
    price = calculate_price(borrowing.book.daily_fee, days, payment_type)
    session = stripe.checkout.Session.create(
        **build_stripe_kwargs(
            request, borrowing.book.title, payment_type, days, price
        )
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


def mark_paid(session_id: str) -> None:
    payment = Payment.objects.filter(
        session_id=session_id,
        status=Payment.PaymentStatus.PENDING,
    ).first()

    if payment:
        payment.status = Payment.PaymentStatus.PAID
        payment.save(update_fields=["status"])
