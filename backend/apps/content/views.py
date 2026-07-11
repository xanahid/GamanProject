from django.shortcuts import get_object_or_404, render

from .models import Article


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    related = Article.objects.filter(is_published=True).exclude(pk=article.pk)[:3]
    return render(request, "content/article_detail.html", {"article": article, "related": related})
