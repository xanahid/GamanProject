from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.models import TimeStampedModel


class Department(TimeStampedModel):
    """دپارتمان‌ها — e.g. زوج و خانواده، نوجوانان. Shown in the nav mega-menu."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Specialty(TimeStampedModel):
    """e.g. اسکیما تراپی، CBT — also shown in the nav mega-menu."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="specialties"
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name


class TherapistProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="therapist_profile"
    )
    photo = models.ImageField(upload_to="therapists/photos/", blank=True, null=True)
    short_bio = models.CharField(max_length=300, help_text="نمایش‌داده‌شده در بلوک‌های پیش‌نمایش")
    full_bio = models.TextField(help_text="نمایش‌داده‌شده در صفحه پروفایل کامل")
    age = models.PositiveSmallIntegerField()
    years_active = models.PositiveSmallIntegerField(default=0)
    specialties = models.ManyToManyField(Specialty, related_name="therapists", blank=True)
    departments = models.ManyToManyField(Department, related_name="therapists", blank=True)

    is_head_of_institute = models.BooleanField(
        default=False,
        help_text="فقط برای دکتر سارا اکبرزاده فعال است — جلسه اول همه مراجعین جدید با ایشان برگزار می‌شود.",
    )
    is_active = models.BooleanField(default=True)

    # Monthly base salary used by the payroll app when computing deductions
    # for late cancellations (see payroll.TherapistCancellation).
    monthly_base_salary = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    class Meta:
        ordering = ["-is_head_of_institute", "-years_active"]

    def __str__(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return reverse("therapists:detail", args=[self.id])

    @property
    def active_client_count(self):
        return self.bookings.filter(client__isnull=False).values("client").distinct().count()
