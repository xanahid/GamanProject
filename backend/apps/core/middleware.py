from django.shortcuts import redirect
from django.urls import reverse


class RoleRedirectMiddleware:
    """
    Keeps each role inside the part of the site meant for them.

    - A therapist who lands on the generic client booking flow gets sent to
      their therapist schedule view instead.
    - Dr. Akbarzadeh's website-content powers (articles, sections) live in
      the Django admin per the spec; this middleware does not touch
      /admin/, it only nudges front-end page access.
    """

    EXEMPT_PREFIXES = ("/admin", "/api", "/static", "/media", "/payments/verify")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            user = getattr(request, "user", None)
            if user and user.is_authenticated and getattr(user, "role", None) == "therapist":
                if path.rstrip("/").endswith("/book") or "book-first-session" in path:
                    return redirect(reverse("scheduling:therapist_schedule"))
        return self.get_response(request)
