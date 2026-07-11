from rest_framework import serializers

from .models import Article, HomepageSection, TherapyMethod


class ArticleSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "slug", "excerpt", "cover_image_url", "published_at"]

    def get_cover_image_url(self, obj):
        return obj.cover_image.url if obj.cover_image else None


class TherapyMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapyMethod
        fields = ["id", "name", "slug", "icon_emoji", "teaser"]


class HomepageSectionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HomepageSection
        fields = [
            "id", "heading", "body", "background_color", "text_color",
            "cta_label", "cta_url", "image_url", "order",
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
