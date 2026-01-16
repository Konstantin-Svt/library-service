from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.SlugRelatedField(read_only=True, slug_field="title")

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date"
        )


class BorrowingDetailSerializer(BorrowingListSerializer):
    book = BookSerializer(read_only=True)
