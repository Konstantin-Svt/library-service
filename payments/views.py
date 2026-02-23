from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from payments.models import Payment
from payments.serializers import PaymentSerializer


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
