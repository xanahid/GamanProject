from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.core.models import TimeStampedModel


class User(AbstractUser):
    """
    Single user table for everyone who can log in: clients, therapists, and
    Dr. Akbarzadeh (head of institute, role='therapist' + is_head flag on her
    TherapistProfile, plus is_staff=True so she also gets Django admin access
    for the website-content powers described in the spec).
    """

    class Role(models.TextChoices):
        CLIENT = "client", "مراجعه‌کننده"
        THERAPIST = "therapist", "درمانگر"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    phone_number = PhoneNumberField(region="IR", unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    

    # Email is the field we actually authenticate with day to day (phone is
    # also accepted at the login form, resolved to this user before auth).
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_therapist(self):
        return self.role == self.Role.THERAPIST


class ClientProfile(TimeStampedModel):
    """Extra fields collected at signup for the مراجعه‌کننده (client) role."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    age = models.PositiveSmallIntegerField(validators=[MinValueValidator(12)])
    occupation = models.CharField(max_length=150, blank=True)

    # Set by Dr. Akbarzadeh after the client's first assessment session.
    # Once populated, the client's booking flow unlocks this therapist's
    # schedule directly instead of forcing them back through her own.
    recommended_therapist = models.ForeignKey(
        "therapists.TherapistProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommended_to_clients",
    )
    has_completed_intake_session = models.BooleanField(default=False)

    def __str__(self):
        return f"پروفایل {self.user}"


class SavedCard(TimeStampedModel):
    """
    A client can save up to 5 cards. We never store a full PAN or CVV —
    only a masked display string and the gateway's reusable token, per
    ZarinPal's tokenized recurring-payment flow. The actual cardholder data
    only ever touches ZarinPal's own hosted payment page.
    """

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_cards")
    masked_pan = models.CharField(max_length=25, help_text="مثال: ۶۲۱۹-۸۶**-****-۱۲۳۴")
    bank_name = models.CharField(max_length=100, blank=True)
    gateway_token = models.CharField(
        max_length=255,
        help_text="توکن قابل استفاده مجدد دریافتی از درگاه پرداخت — هرگز شماره کارت کامل ذخیره نمی‌شود.",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.masked_pan} ({self.client})"

    def save(self, *args, **kwargs):
        # Enforce the "max 5 saved cards" rule at the model layer too, not
        # just in the API serializer, so it holds regardless of entry point.
        if self._state.adding:
            existing = SavedCard.objects.filter(client=self.client).count()
            if existing >= 5:
                raise ValueError("حداکثر تعداد کارت‌های ذخیره‌شده (۵ عدد) است.")
        super().save(*args, **kwargs)
