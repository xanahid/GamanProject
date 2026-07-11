from rest_framework_simplejwt.views import TokenRefreshView
from django.urls import path

from . import api_views

app_name = "accounts_api"

urlpatterns = [
    path("signup/", api_views.SignupView.as_view(), name="signup"),
    path("login/", api_views.LoginView.as_view(), name="login"),
    path("login/refresh/", TokenRefreshView.as_view(), name="login_refresh"),
    path("me/", api_views.MyProfileView.as_view(), name="my_profile"),
    path("me/dashboard/", api_views.MyDashboardSummaryView.as_view(), name="my_dashboard"),
    path("me/cards/", api_views.SavedCardListCreateView.as_view(), name="saved_cards"),
    path("me/cards/<int:pk>/", api_views.SavedCardDeleteView.as_view(), name="saved_card_delete"),
]
