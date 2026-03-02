from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import PaymentsViewSet, stripe_webhook

router = DefaultRouter()
router.register("", PaymentsViewSet, basename="payment")

app_name = "payments"

urlpatterns = [
    path("stripe-webhook/", stripe_webhook, name="stripe_webhook"),
    path("", include(router.urls)),
]
