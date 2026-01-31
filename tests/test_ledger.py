import pytest
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db

def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

def test_deposit_idempotent(api_client):
    user = User.objects.create_user(username="u1", password="pass")
    c = auth_client(api_client, user)

    headers = {"HTTP_IDEMPOTENCY_KEY": "abc-1"}
    r1 = c.post("/api/transactions/deposit/", {"amount": "10.5"}, format="json", **headers)
    assert r1.status_code == 200

    bal1 = c.get("/api/wallet/").json()["balance"]

    r2 = c.post("/api/transactions/deposit/", {"amount": "10.5"}, format="json", **headers)
    assert r2.status_code == 200
    bal2 = c.get("/api/wallet/").json()["balance"]

    assert r1.json()["id"] == r2.json()["id"]
    assert bal1 == bal2  # balance must NOT increase twice

def test_withdraw_insufficient_funds(api_client):
    user = User.objects.create_user(username="u2", password="pass")
    c = auth_client(api_client, user)

    r = c.post("/api/transactions/withdraw/", {"amount": "1"}, format="json", HTTP_IDEMPOTENCY_KEY="w-1")
    assert r.status_code == 400

def test_withdraw_success(api_client):
    user = User.objects.create_user(username="u3", password="pass")
    c = auth_client(api_client, user)

    c.post("/api/transactions/deposit/", {"amount": "5"}, format="json", HTTP_IDEMPOTENCY_KEY="d-1")
    r = c.post("/api/transactions/withdraw/", {"amount": "2"}, format="json", HTTP_IDEMPOTENCY_KEY="w-2")
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    bal = c.get("/api/wallet/").json()["balance"]
    assert bal == "3.00000000"
