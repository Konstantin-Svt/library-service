from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import PaymentsViewSet

router = DefaultRouter()
router.register("", PaymentsViewSet, basename="payment")

app_name = "payments"

urlpatterns = [
    path("", include(router.urls)),
]
