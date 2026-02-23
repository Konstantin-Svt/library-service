from datetime import date

from django.core.validators import MinValueValidator
from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing, validate_borrowing_dates
from payments.serializers import PaymentSerializer


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.SlugRelatedField(
        slug_field="title", queryset=Book.objects.all()
    )
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "payments"
        )
        read_only_fields = ("id", "user", "actual_return_date", "payments")


class BorrowingDetailSerializer(BorrowingListSerializer):
    book = BookSerializer(read_only=True)


class BorrowingCreateSerializer(BorrowingListSerializer):
    borrow_date = serializers.DateField(
        validators=[MinValueValidator(date.today)]
    )
    expected_return_date = serializers.DateField(
        validators=[MinValueValidator(date.today)]
    )

    def validate(self, data):
        super().validate(data)
        validate_borrowing_dates(
            data["borrow_date"],
            data["expected_return_date"],
            None,
            serializers.ValidationError,
        )
        return data
