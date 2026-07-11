from django.contrib import admin
from django.utils.html import format_html

from .models import Article, HomepageSection, TherapyMethod


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "show_in_slideshow", "published_at", "author")
    list_filter = ("is_published", "show_in_slideshow")
    search_fields = ("title", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(TherapyMethod)
class TherapyMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "is_published", "order")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("order",)


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    list_display = ("heading", "color_preview", "order", "is_visible")
    list_editable = ("order", "is_visible")
    fields = (
        "heading", "body", "background_color", "text_color",
        "cta_label", "cta_url", "image", "order", "is_visible",
    )

    @admin.display(description="پیش‌نمایش رنگ")
    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:60px;height:20px;'
            'background:{};border:1px solid #ccc;border-radius:4px;"></span>',
            obj.background_color,
        )
