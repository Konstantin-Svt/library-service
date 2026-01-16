from django.db import transaction
from django.db.models import F
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

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
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        elif self.action == "retrieve":
            return BorrowingDetailSerializer
        else:
            return BorrowingCreateSerializer

    def get_queryset(self):
        qs = self.queryset

        if self.action == "list":
            is_active = self.request.query_params.get("is_active")
            if is_active and is_active.lower() in (
                "true",
                "yes",
                "1",
                "active",
                "y",
            ):
                qs = qs.filter(actual_return_date=None)
            elif is_active and is_active.lower() in (
                "false",
                "no",
                "not",
                "0",
                "inactive",
                "n",
            ):
                qs = qs.exclude(actual_return_date=None)

            user_id = self.request.query_params.get("user_id")
            if user_id:
                qs = qs.filter(user=user_id)

        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

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
