from django.shortcuts import render

from apps.content.models import Article, HomepageSection, TherapyMethod
from apps.therapists.models import TherapistProfile


def home(request):
    """
    Homepage: slideshow of articles, therapist preview grid, therapy
    methods section, plus any extra sections Dr. Akbarzadeh has added
    through the Django admin (each with its own background color and
    heading, ordered by `order`).
    """
    slideshow_articles = (
        Article.objects.filter(is_published=True, show_in_slideshow=True)
        .order_by("-published_at")[:5]
    )
    featured_therapists = (
        TherapistProfile.objects.filter(is_active=True)
        .select_related("user")
        .order_by("-is_head_of_institute", "-years_active")[:8]
    )
    therapy_methods = TherapyMethod.objects.filter(is_published=True)
    extra_sections = HomepageSection.objects.filter(is_visible=True).order_by("order")

    context = {
        "slideshow_articles": slideshow_articles,
        "featured_therapists": featured_therapists,
        "therapy_methods": therapy_methods,
        "extra_sections": extra_sections,
    }
    return render(request, "home/index.html", context)


def therapy_method_detail(request, slug):
    from apps.content.models import TherapyMethod

    method = TherapyMethod.objects.get(slug=slug, is_published=True)
    return render(request, "content/method_detail.html", {"method": method})
