from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import ClientProfile, SavedCard, User

# Customize the Django admin site for Dr. Akbarzadeh
admin.site.site_header = "گمان — پنل مدیریت"
admin.site.site_title = "گمان Admin"
admin.site.index_title = "مدیریت محتوا و سایت"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "get_full_name", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email", "phone_number")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("اطلاعات گمان", {"fields": ("role", "phone_number")}),
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "occupation", "recommended_therapist", "has_completed_intake_session")
    list_filter = ("has_completed_intake_session", "recommended_therapist")
    search_fields = ("user__first_name", "user__last_name", "user__email")
    autocomplete_fields = ("user", "recommended_therapist")


@admin.register(SavedCard)
class SavedCardAdmin(admin.ModelAdmin):
    list_display = ("client", "masked_pan", "bank_name", "is_default", "created_at")
    search_fields = ("client__first_name", "client__last_name", "masked_pan")
    readonly_fields = ("gateway_token",)
