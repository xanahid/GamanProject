from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Non-translated URLs: API, admin, i18n switcher, health check
urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),   # provides set_language view
    path("api/v1/accounts/", include("apps.accounts.api_urls")),
    path("api/v1/therapists/", include("apps.therapists.api_urls")),
    path("api/v1/scheduling/", include("apps.scheduling.api_urls")),
    path("api/v1/payments/", include("apps.payments.api_urls")),
    path("api/v1/content/", include("apps.content.api_urls")),
    path("api/v1/notes/", include("apps.notes.api_urls")),
    path("api/v1/payroll/", include("apps.payroll.api_urls")),
    path("payments/verify/", include("apps.payments.callback_urls")),
    path("healthz/", include("apps.core.health_urls")),
]

# Translated, server-rendered pages (Farsi default, English at /en/...)
urlpatterns += i18n_patterns(
    path("", include("apps.core.urls")),
    path("therapists/", include("apps.therapists.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("articles/", include("apps.content.urls")),
    path("schedule/", include("apps.scheduling.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
