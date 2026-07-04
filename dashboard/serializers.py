from rest_framework import serializers


class LowStockItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    stock = serializers.IntegerField()


class OverviewSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.FloatField()
    orders_by_status = serializers.DictField(child=serializers.IntegerField())
    revenue_this_month = serializers.FloatField()
    average_order_value = serializers.FloatField()
    total_products = serializers.IntegerField()
    total_users = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    low_stock_products = LowStockItemSerializer(many=True)


class BestSellerItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    total_quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_stock = serializers.IntegerField()