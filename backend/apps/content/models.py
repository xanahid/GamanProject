from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Article(TimeStampedModel):
    """
    Articles Dr. Akbarzadeh (or any admin) adds/removes from the Django
    admin. Shown as slideshow previews on the homepage with a
    'بیشتر بخوانید' button leading to the full article page.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    excerpt = models.CharField(max_length=300, help_text="نمایش‌داده‌شده در پیش‌نمایش اسلایدشو")
    body = models.TextField()
    cover_image = models.ImageField(upload_to="articles/covers/", blank=True, null=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    is_published = models.BooleanField(default=True)
    show_in_slideshow = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:article_detail", args=[self.slug])


class TherapyMethod(TimeStampedModel):
    """
    'روش‌های درمانی' section — short teaser + 'بیشتر بخوانید' to a full
    page, per spec.
    """

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    icon_emoji = models.CharField(max_length=10, default="🧠", help_text="ایموجی نمایش‌داده‌شده روی کارت")
    teaser = models.CharField(max_length=300)
    full_description = models.TextField()
    is_published = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Therapy methods"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("core:method_detail", args=[self.slug])


class HomepageSection(TimeStampedModel):
    """
    Lets the admin (Dr. Akbarzadeh, via Django admin) append arbitrary
    extra sections to the homepage below the built-in ones, each with its
    own heading, body, and background color — exactly the
    "more sections could be added by the admin... choose the background
    color... and header" capability from the spec.
    """

    heading = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    background_color = models.CharField(
        max_length=20, default="#FFFFFF",
        help_text="کد رنگ هگز برای پس‌زمینه این بخش، مثل #E1F5EE",
    )
    text_color = models.CharField(max_length=20, default="#1A1A18")
    cta_label = models.CharField(max_length=80, blank=True, help_text="متن دکمه اختیاری")
    cta_url = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="homepage_sections/", blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.heading
