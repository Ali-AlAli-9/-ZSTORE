from django.urls import path
from .views import OrderListView, OrderDetailView, CheckoutView, CancelOrderView,AdminOrderListView, AdminOrderDetailView

urlpatterns = [
    path("", OrderListView.as_view()),
    path("<int:order_id>/", OrderDetailView.as_view()),
    path("checkout/", CheckoutView.as_view()),
    path("<int:order_id>/cancel/", CancelOrderView.as_view()),
    path("admin-orders/", AdminOrderListView.as_view()),
    path("admin-orders/<int:order_id>/", AdminOrderDetailView.as_view()),
]
