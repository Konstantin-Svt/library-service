from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.services import is_paid


class PaymentsViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAuthenticated,)
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related("borrowing")
        if self.request.user.is_staff:
            return qs
        return qs.filter(borrowing__user=self.request.user)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=(IsAuthenticated,),
        serializer_class=None,
        url_path="success",
        url_name="success",
    )
    def payment_success(self, request):
        session_id = self.request.query_params.get("session_id")
        if not session_id:
            raise ValidationError("session_id query param is required")

        try:
            payment = Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            raise ValidationError("Payment does not exist.")

        if is_paid(session_id):
            if payment.status == Payment.PaymentStatus.PENDING:
                payment.status = Payment.PaymentStatus.PAID
                payment.save(update_fields=["status"])
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        return Response(
            {"status": "failure"}, status=status.HTTP_402_PAYMENT_REQUIRED
        )

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=(IsAuthenticated,),
        serializer_class=None,
        url_path="cancel",
        url_name="cancel",
    )
    def payment_cancel(self, request):
        session_id = self.request.query_params.get("session_id")
        if not session_id:
            raise ValidationError("session_id query param is required")

        try:
            Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            raise ValidationError("Payment does not exist.")

        return Response(
            {
                "status": "canceled, can be paid later (session is valid for 24h)"
            },
            status=status.HTTP_200_OK,
        )
