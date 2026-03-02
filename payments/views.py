import stripe
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.conf import settings
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.services import mark_paid


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="session_id",
                description="Stripe session ID",
                type=OpenApiTypes.STR,
                required=True
            )
        ]
    )
    @action(
        detail=False,
        methods=["GET"],
        permission_classes=(IsAuthenticated,),
        serializer_class=None,
        url_path="success",
        url_name="success",
    )
    def payment_success(self, request):
        """
        Endpoint for Stripe success-url redirect.
        """
        session_id = self.request.query_params.get("session_id")
        if not session_id:
            raise ValidationError("session_id query param is required")

        payment = get_object_or_404(self.get_queryset(), session_id=session_id)

        return Response(
            {"status": payment.get_status_display()}, status=status.HTTP_200_OK
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="session_id",
                description="Stripe session ID",
                type=OpenApiTypes.STR,
                required=True
            )
        ]
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
        """
        Endpoint for Stripe cancel-url redirect.
        """
        session_id = self.request.query_params.get("session_id")
        if not session_id:
            raise ValidationError("session_id query param is required")

        get_object_or_404(self.get_queryset(), session_id=session_id)

        return Response(
            {
                "status": "canceled, can be paid later "
                "(session is valid for 24h)"
            },
            status=status.HTTP_200_OK,
        )


@csrf_exempt
@api_view(http_method_names=["POST"])
def stripe_webhook(request):
    """
    Endpoint for Stripe 'successful payment' event webhook.
    Should not be used by frontend directly.
    """
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if (
        event["type"] == "checkout.session.completed"
        or event["type"] == "checkout.session.async_payment_succeeded"
    ):
        mark_paid(event["data"]["object"]["id"])

    return Response(status=status.HTTP_200_OK)
