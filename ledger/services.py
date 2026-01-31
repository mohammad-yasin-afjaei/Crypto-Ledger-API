from decimal import Decimal
from django.db import transaction as db_tx
from django.db.utils import IntegrityError
from .models import Wallet, Transaction

IDEMPOTENCY_HEADER = "HTTP_IDEMPOTENCY_KEY"  # Django adds HTTP_ prefix

class InsufficientFunds(Exception):
    pass

def _get_idempotency_key(request) -> str:
    key = request.META.get(IDEMPOTENCY_HEADER, "")
    return (key or "").strip()

@db_tx.atomic
def deposit(*, user, amount: Decimal, idem_key: str) -> Transaction:
    if not idem_key:
        raise ValueError("Missing Idempotency-Key")

    # idempotency fast path
    existing = Transaction.objects.filter(user=user, idempotency_key=idem_key).first()
    if existing:
        return existing

    wallet = Wallet.objects.select_for_update().get(user=user)
    wallet.balance = wallet.balance + amount
    wallet.save(update_fields=["balance"])

    try:
        tx = Transaction.objects.create(
            user=user,
            wallet=wallet,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.SUCCESS,
            amount=amount,
            idempotency_key=idem_key,
        )
    except IntegrityError:
        # race: another request created it
        return Transaction.objects.get(user=user, idempotency_key=idem_key)

    return tx

@db_tx.atomic
def withdraw(*, user, amount: Decimal, idem_key: str) -> Transaction:
    if not idem_key:
        raise ValueError("Missing Idempotency-Key")

    existing = Transaction.objects.filter(user=user, idempotency_key=idem_key).first()
    if existing:
        return existing

    wallet = Wallet.objects.select_for_update().get(user=user)

    if wallet.balance < amount:
        # record failed tx (still idempotent)
        try:
            tx = Transaction.objects.create(
                user=user,
                wallet=wallet,
                type=Transaction.Type.WITHDRAW,
                status=Transaction.Status.FAILED,
                amount=amount,
                idempotency_key=idem_key,
            )
        except IntegrityError:
            return Transaction.objects.get(user=user, idempotency_key=idem_key)
        raise InsufficientFunds()

    wallet.balance = wallet.balance - amount
    wallet.save(update_fields=["balance"])

    try:
        tx = Transaction.objects.create(
            user=user,
            wallet=wallet,
            type=Transaction.Type.WITHDRAW,
            status=Transaction.Status.SUCCESS,
            amount=amount,
            idempotency_key=idem_key,
        )
    except IntegrityError:
        return Transaction.objects.get(user=user, idempotency_key=idem_key)

    return tx
