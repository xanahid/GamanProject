from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

User = get_user_model()


def _redirect_after_login(user, next_url=""):
    """Send each role to the right place after login."""
    if next_url:
        return redirect(next_url)
    if user.is_therapist:
        profile = getattr(user, "therapist_profile", None)
        if profile and profile.is_head_of_institute:
            return redirect("core:head_dashboard")
        return redirect("scheduling:therapist_schedule")
    return redirect("core:home")


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")
        user_obj = (
            User.objects.filter(email__iexact=identifier).first()
            or User.objects.filter(phone_number=identifier).first()
        )
        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None
        if user is not None:
            login(request, user)
            return _redirect_after_login(user, next_url)
        messages.error(request, _("شماره موبایل/ایمیل یا رمز عبور اشتباه است."))

    return render(request, "accounts/login.html", {"next": next_url})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    return render(request, "accounts/signup.html")


def logout_view(request):
    logout(request)
    return redirect("core:home")


def profile_view(request):
    """Client's own profile panel: upcoming sessions, saved cards, recommended therapist."""
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next={request.path}")
    # Head of institute should use the dedicated dashboard
    if request.user.is_therapist:
        profile = getattr(request.user, "therapist_profile", None)
        if profile and profile.is_head_of_institute:
            return redirect("core:head_dashboard")
        return redirect("scheduling:therapist_schedule")
    return render(request, "accounts/profile.html")
