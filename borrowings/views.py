from django.db import transaction
from django.db.models import F
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
)


class BorrowingViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book")

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        elif self.action == "retrieve":
            return BorrowingDetailSerializer
        else:
            return BorrowingCreateSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            book = Book.objects.select_for_update().get(
                pk=serializer.validated_data["book"].id
            )
            if book.inventory < 1:
                raise ValidationError(f"No more books '{book.title}' left!")
            book.inventory = F("inventory") - 1
            book.save(update_fields=["inventory"])
            serializer.save(user=self.request.user)
