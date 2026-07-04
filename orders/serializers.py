from .models import Order, OrderItem
from rest_framework import serializers


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity", "price"]
        read_only_fields = ["id"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "items", "created_at", "updated_at", "shipping_address", "status", "total_price", "phone", "payment_method", "payment_status", "full_name"]
        read_only_fields = ["id", "user", "status", "total_price", "created_at", "payment_status"]


    def validate_shipping_address(self, value):
     if len(value.strip()) < 10:
        raise serializers.ValidationError("Shipping address is too short")
     return value
 
    def validate_phone(self, value):
     if not value.isdigit():
        raise serializers.ValidationError("Phone must contain only digits")
     if len(value) < 7:
        raise serializers.ValidationError("Phone number is too short")
     return value
 
    def validate(self, attrs):
     if attrs.get("shipping_address") and attrs.get("phone"):
        return attrs
     raise serializers.ValidationError("Shipping address and phone are required")


class AdminOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    payment_status = serializers.ChoiceField(choices=Order.PAYMENT_STATUS_CHOICES)

    class Meta:
        model = Order
        fields = ["id", "user", "username", "email", "created_at", "updated_at", "shipping_address", "status", "total_price", "phone", "payment_method", "payment_status", "full_name", "is_archived", "items"]
        read_only_fields = ["id", "user", "total_price", "created_at"]

    def validate_status(self, value):
        if self.instance and value != self.instance.status:
            valid_next = self.instance.VALID_TRANSITIONS.get(self.instance.status, [])
            if value not in valid_next:
                raise serializers.ValidationError(
                    f"Cannot change status from '{self.instance.status}' to '{value}'. "
                    f"Allowed transitions: {', '.join(valid_next) if valid_next else 'none'}"
                )
        return value
  
