from datetime import date

import django.core.exceptions
from django.db import transaction
from django.db.models import F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
)
from payments.models import Payment
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
            if is_active is not None:
                if is_active == "1":
                    qs = qs.filter(actual_return_date=None)
                elif is_active == "0":
                    qs = qs.exclude(actual_return_date=None)
                else:
                    raise ValidationError("Invalid value for is_active")

            user_id = self.request.query_params.get("user_id")
            if user_id:
                qs = qs.filter(user=user_id)

        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.INT,
                description="Whether the borrowing is "
                            "active (absent actual_return_date = book "
                            "is not returned) or not. Accepts 1 for "
                            "active and 0 for inactive.",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
            create_stripe_payment(self.request, borrowing)

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=(IsAuthenticated,),
        url_path="return",
        url_name="return",
    )
    def return_book(self, request, *args, **kwargs):
        """
        Endpoint to return a borrowed book.
        """
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            raise ValidationError(
                {"actual_return_date": "The book is already returned."}
            )

        with transaction.atomic():
            borrowing.actual_return_date = date.today()
            try:
                borrowing.save(update_fields=["actual_return_date"])
            except django.core.exceptions.ValidationError as e:
                raise ValidationError(str(e))

            borrowing.book.inventory = F("inventory") + 1
            borrowing.book.save(update_fields=["inventory"])
            response_text = {"status": "ok"}

            if borrowing.actual_return_date > borrowing.expected_return_date:
                payment = create_stripe_payment(
                    self.request,
                    borrowing,
                    payment_type=Payment.PaymentType.FINE,
                )
                response_text["status"] = (
                    "overdue, pay the fine with multiplier"
                )
                response_text["session_url"] = payment.session_url

            return Response(response_text, status=status.HTTP_200_OK)
