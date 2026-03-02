from django.urls import path, include
from rest_framework.routers import DefaultRouter

from borrowings.views import BorrowingViewSet

router = DefaultRouter()
router.register("", BorrowingViewSet, basename="borrowing")

app_name = "borrowings"

urlpatterns = [
    path("", include(router.urls)),
]
