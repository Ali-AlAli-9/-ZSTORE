from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from . import analytics

from .serializers import OverviewSerializer, BestSellerItemSerializer


class DashboardOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = {
            "total_orders": analytics.total_orders(),
            "total_revenue": analytics.total_revenue(),
            "orders_by_status": analytics.orders_by_status(),
            "revenue_this_month": analytics.revenue_this_month(),
            "average_order_value": analytics.average_order_value(),
            "total_products": analytics.total_products(),
            "total_users": analytics.total_users(),
            "new_users_this_month": analytics.new_users_this_month(),
            "low_stock_products": analytics.low_stock_products(),
        }
        serializer = OverviewSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    
class BestSellersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = request.query_params.get("limit", 10)
        try:
            limit = min(int(limit), 50)
        except (ValueError, TypeError):
            limit = 10

        items = analytics.best_sellers(limit=limit)
        data = [
            {
                "product_id": item["pid"],
                "name": item["name"],
                "total_quantity_sold": item["total_quantity"],
                "total_revenue": item["total_revenue"],
                "current_stock": item["stock"],
            }
            for item in items
        ]
        serializer = BestSellerItemSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)