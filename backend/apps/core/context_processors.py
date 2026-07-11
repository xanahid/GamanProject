from django.conf import settings
from django.urls import reverse


def site_settings(request):
    """Values every template needs: current language, RTL flag, brand info, footer links."""
    is_rtl = request.LANGUAGE_CODE == "fa"

    footer_links = {
        ("خدمات" if is_rtl else "Services"): [
            ("جلسه فردی" if is_rtl else "Individual Session", "/schedule/book/"),
            ("زوج‌درمانی" if is_rtl else "Couples Therapy", "/therapists/?department=couples-family"),
            ("روانشناسی نوجوان" if is_rtl else "Adolescent Psychology", "/therapists/?department=teens"),
        ],
        ("گمان" if is_rtl else "Gaman"): [
            ("درمانگران" if is_rtl else "Therapists", "/therapists/"),
            ("مقالات" if is_rtl else "Articles", "/"),
            ("درباره ما" if is_rtl else "About", "/"),
        ],
        ("پشتیبانی" if is_rtl else "Support"): [
            ("سؤالات متداول" if is_rtl else "FAQ", "#"),
            ("سیاست لغو" if is_rtl else "Cancellation Policy", "#"),
            ("حریم خصوصی" if is_rtl else "Privacy", "#"),
        ],
    }

    return {
        "SITE_NAME": "گمان" if is_rtl else "Gaman",
        "SITE_DIR": "rtl" if is_rtl else "ltr",
        "CURRENT_LANG": request.LANGUAGE_CODE,
        "SESSION_DURATION_MINUTES": settings.SESSION_DURATION_MINUTES,
        "footer_links": footer_links,
    }
