from rest_framework import viewsets, mixins

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)


class BorrowingViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Borrowing.objects.select_related("book")

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        elif self.action == "retrieve":
            return BorrowingDetailSerializer
