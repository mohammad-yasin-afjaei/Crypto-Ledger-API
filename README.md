# Crypto Ledger API
![CI](https://github.com/mohammad-yasin-afjaei/Crypto-Ledger-API/actions/workflows/ci.yml/badge.svg)

A Django REST API for managing crypto wallets with deposits, withdrawals, and transaction history. Uses idempotency keys for safe retries.

## Setup

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DB URL, SECRET_KEY, etc.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API Endpoints

All endpoints require authentication (Session or Basic Auth).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wallet/` | Get current balance |
| POST | `/api/deposit/` | Deposit funds (idempotent) |
| POST | `/api/withdraw/` | Withdraw funds (idempotent) |
| GET | `/api/transactions/` | List recent transactions |

### Deposit / Withdraw

```json
POST /api/deposit/
{
  "amount": "1.5",
  "idempotency_key": "unique-key-per-request"
}
```

Reusing the same `idempotency_key` returns the original transaction without creating a duplicate.
