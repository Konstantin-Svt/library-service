from datetime import date

from django.db import transaction
from django.db.models import F
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
)
from payments.services import create_stripe_payment


class BorrowingViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book").prefetch_related(
        "payments"
    )
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

            borrowing = serializer.save(user=self.request.user)
            create_stripe_payment(borrowing)

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=(IsAdminUser,),
        url_path="return",
        url_name="return",
    )
    def return_book(self, request, *args, **kwargs):
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            raise ValidationError(
                {"actual_return_date": "The book is already returned."}
            )

        with transaction.atomic():
            borrowing.actual_return_date = date.today()
            borrowing.save(update_fields=["actual_return_date"])

            borrowing.book.inventory = F("inventory") + 1
            borrowing.book.save(update_fields=["inventory"])

            return Response(status=status.HTTP_204_NO_CONTENT)
