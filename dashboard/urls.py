from django.urls import path
from .views import DashboardOverviewView, BestSellersView

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("best-sellers/", BestSellersView.as_view(), name="dashboard-best-sellers"),
]