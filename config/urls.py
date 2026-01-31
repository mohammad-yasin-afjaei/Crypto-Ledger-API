from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ledger.views import WalletViewSet, TransactionViewSet

router = DefaultRouter()
router.register("wallet", WalletViewSet, basename="wallet")
router.register("transactions", TransactionViewSet, basename="transactions")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
