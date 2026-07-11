from django.urls import path

from . import api_views

app_name = "payments_api"

urlpatterns = [
    path("initiate/", api_views.PaymentInitiateView.as_view(), name="initiate"),
    path("checkout-cards/", api_views.MyCardsForCheckoutView.as_view(), name="checkout_cards"),
]
