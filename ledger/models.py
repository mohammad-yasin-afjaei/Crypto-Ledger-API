from decimal import Decimal

from django.conf import settings
from django.db import models

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0"))

    def __str__(self) -> str:
        return f"Wallet(user={self.user_id}, balance={self.balance})"


class Transaction(models.Model):
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAW = "withdraw", "Withdraw"

    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")

    type = models.CharField(max_length=16, choices=Type.choices)
    status = models.CharField(max_length=16, choices=Status.choices)

    amount = models.DecimalField(max_digits=20, decimal_places=8)
    idempotency_key = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "idempotency_key"], name="uniq_user_idempotency_key")
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["type", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Tx(user={self.user_id}, type={self.type}, amount={self.amount}, status={self.status})"
