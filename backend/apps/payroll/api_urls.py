from django.urls import path

from . import api_views

app_name = "payroll_api"

urlpatterns = [
    path("my-summaries/", api_views.MyPayrollSummaryView.as_view(), name="my_summaries"),
    path("my-cancellations/", api_views.MyCancellationsView.as_view(), name="my_cancellations"),
]
