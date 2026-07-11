from rest_framework import serializers

from .models import Payment, RefundRequest


class PaymentInitiateSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    saved_card_id = serializers.IntegerField(required=False, allow_null=True)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "booking", "amount_rials", "status", "gateway",
            "card_pan_masked", "paid_at", "created_at",
        ]
        read_only_fields = fields


class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ["id", "payment", "reason", "amount_rials", "is_settled", "settled_at"]
        read_only_fields = fields
