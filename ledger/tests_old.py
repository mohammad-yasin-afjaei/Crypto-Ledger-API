from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

import pytest

from .models import Transaction, Wallet

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestWalletView:
    def test_get_wallet_creates_wallet_and_returns_balance(self, api_client):
        response = api_client.get("/api/wallet/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["balance"] == "0.00000000"

    def test_get_wallet_returns_updated_balance_after_deposit(self, api_client):
        api_client.post(
            "/api/deposit/",
            {"amount": "10.5", "idempotency_key": "dep-1"},
            format="json",
        )
        response = api_client.get("/api/wallet/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["balance"] == "10.50000000"


class TestDepositView:
    def test_deposit_creates_transaction_and_updates_balance(self, api_client, user):
        response = api_client.post(
            "/api/deposit/",
            {"amount": "1.5", "idempotency_key": "dep-1"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "deposit"
        assert response.data["status"] == "success"
        assert response.data["amount"] == "1.50000000"

        wallet = Wallet.objects.get(user=user)
        assert wallet.balance == Decimal("1.5")

    def test_deposit_idempotent_returns_existing_on_duplicate_key(self, api_client, user):
        api_client.post(
            "/api/deposit/",
            {"amount": "2.0", "idempotency_key": "dep-same"},
            format="json",
        )
        response = api_client.post(
            "/api/deposit/",
            {"amount": "2.0", "idempotency_key": "dep-same"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["amount"] == "2.00000000"

        assert Transaction.objects.filter(idempotency_key="dep-same").count() == 1
        wallet = Wallet.objects.get(user=user)
        assert wallet.balance == Decimal("2.0")

    def test_deposit_invalid_amount_rejected(self, api_client):
        response = api_client.post(
            "/api/deposit/",
            {"amount": "0", "idempotency_key": "dep-zero"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestWithdrawView:
    def test_withdraw_succeeds_when_sufficient_balance(self, api_client, user):
        api_client.post(
            "/api/deposit/",
            {"amount": "5.0", "idempotency_key": "dep-1"},
            format="json",
        )
        response = api_client.post(
            "/api/withdraw/",
            {"amount": "2.0", "idempotency_key": "wd-1"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "withdraw"
        assert response.data["amount"] == "2.00000000"

        wallet = Wallet.objects.get(user=user)
        assert wallet.balance == Decimal("3.0")

    def test_withdraw_fails_when_insufficient_balance(self, api_client):
        response = api_client.post(
            "/api/withdraw/",
            {"amount": "100", "idempotency_key": "wd-1"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient balance" in response.data["detail"]

    def test_withdraw_idempotent_returns_existing_on_duplicate_key(self, api_client, user):
        api_client.post(
            "/api/deposit/",
            {"amount": "10", "idempotency_key": "dep-1"},
            format="json",
        )
        api_client.post(
            "/api/withdraw/",
            {"amount": "3", "idempotency_key": "wd-same"},
            format="json",
        )
        response = api_client.post(
            "/api/withdraw/",
            {"amount": "3", "idempotency_key": "wd-same"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        assert Transaction.objects.filter(idempotency_key="wd-same").count() == 1
        wallet = Wallet.objects.get(user=user)
        assert wallet.balance == Decimal("7")


class TestTransactionListView:
    def test_transactions_returns_list(self, api_client):
        response = api_client.get("/api/transactions/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_transactions_shows_deposits_and_withdrawals(self, api_client):
        api_client.post(
            "/api/deposit/",
            {"amount": "1", "idempotency_key": "dep-1"},
            format="json",
        )
        api_client.post(
            "/api/withdraw/",
            {"amount": "0.5", "idempotency_key": "wd-1"},
            format="json",
        )
        response = api_client.get("/api/transactions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


class TestAuthRequired:
    def test_wallet_requires_auth(self, user):
        client = APIClient()
        response = client.get("/api/wallet/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
