from rest_framework import generics, permissions

from .models import Article, HomepageSection, TherapyMethod
from .serializers import ArticleSerializer, HomepageSectionSerializer, TherapyMethodSerializer


class ArticleListAPIView(generics.ListAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Article.objects.filter(is_published=True)


class TherapyMethodListAPIView(generics.ListAPIView):
    serializer_class = TherapyMethodSerializer
    permission_classes = [permissions.AllowAny]
    queryset = TherapyMethod.objects.filter(is_published=True)


class HomepageSectionListAPIView(generics.ListAPIView):
    serializer_class = HomepageSectionSerializer
    permission_classes = [permissions.AllowAny]
    queryset = HomepageSection.objects.filter(is_visible=True)
