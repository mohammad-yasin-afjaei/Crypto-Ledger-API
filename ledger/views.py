from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Wallet

from .models import Transaction
from .serializers import TransactionSerializer, MoneyInputSerializer, WalletSerializer
from .services import deposit, withdraw, _get_idempotency_key, InsufficientFunds

class WalletViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        wallet = Wallet.objects.get(user=request.user)  # fresh from DB (no cached relation)
        return Response(WalletSerializer(wallet).data)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=False, methods=["post"])
    def deposit(self, request):
        idem = _get_idempotency_key(request)
        s = MoneyInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tx = deposit(user=request.user, amount=s.validated_data["amount"], idem_key=idem)
        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def withdraw(self, request):
        idem = _get_idempotency_key(request)
        s = MoneyInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            tx = withdraw(user=request.user, amount=s.validated_data["amount"], idem_key=idem)
            return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)
        except InsufficientFunds:
            # still return the created FAILED tx if it exists (idempotent behavior)
            tx = Transaction.objects.filter(user=request.user, idempotency_key=idem).first()
            payload = TransactionSerializer(tx).data if tx else {"detail": "Insufficient funds"}
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"detail": "Missing Idempotency-Key header"}, status=status.HTTP_400_BAD_REQUEST)
