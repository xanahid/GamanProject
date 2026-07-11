from django.contrib import admin
from django.utils import timezone

from .models import Payment, RefundRequest


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "amount_rials", "status", "gateway", "ref_id", "paid_at")
    list_filter = ("status", "gateway")
    search_fields = ("client__first_name", "client__last_name", "authority", "ref_id")
    readonly_fields = ("authority", "ref_id", "card_pan_masked", "paid_at")
    autocomplete_fields = ("client", "booking")


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ("payment", "reason", "amount_rials", "is_settled", "settled_at")
    list_filter = ("reason", "is_settled")
    actions = ["mark_settled"]

    @admin.action(description="علامت‌گذاری به‌عنوان تسویه‌شده")
    def mark_settled(self, request, queryset):
        updated = queryset.update(is_settled=True, settled_at=timezone.now())
        for refund in queryset:
            refund.payment.status = refund.payment.Status.REFUNDED
            refund.payment.save(update_fields=["status"])
        self.message_user(request, f"{updated} مورد تسویه شد.")
