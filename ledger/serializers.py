from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from .models import Transaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["balance"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "type", "status", "amount", "idempotency_key", "created_at"]


class MoneyInputSerializer(serializers.Serializer):
    amount = serializers.CharField()

    def validate_amount(self, value: str) -> Decimal:
        try:
            amt = Decimal(value)
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Invalid decimal amount.")
        if amt <= 0:
            raise serializers.ValidationError("Amount must be > 0.")
        return amt


class DepositWithdrawSerializer(MoneyInputSerializer):
    """Extends MoneyInputSerializer with idempotency_key for deposit/withdraw endpoints."""

    idempotency_key = serializers.CharField(max_length=128)
