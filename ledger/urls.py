from django.urls import path

from . import views

urlpatterns = [
    path("wallet/", views.WalletView.as_view(), name="wallet"),
    path("deposit/", views.DepositView.as_view(), name="deposit"),
    path("withdraw/", views.WithdrawView.as_view(), name="withdraw"),
    path("transactions/", views.TransactionListView.as_view(), name="transactions"),
]
