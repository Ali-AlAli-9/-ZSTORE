from .models import Product
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "stock", "image", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_price(self, value):
     if value <= 0:
        raise serializers.ValidationError("Price must be greater than 0")
     return value
 
 
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value
    
class PublicProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "image", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_price(self, value):
     if value <= 0:
        raise serializers.ValidationError("Price must be greater than 0")
     return value