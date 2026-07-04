from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework import status,generics
from .models import Order, OrderItem
from .serializers import OrderSerializer, AdminOrderSerializer
from cart.models import Cart
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from products.models import Product

# Create your views here.


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.select_related('user').prefetch_related('items').filter(user=self.request.user).order_by("-created_at")


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    @transaction.atomic
    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if "payment_method" in request.data:
            payment_m = request.data["payment_method"]
            valid = dict(Order.PAYMENT_METHOD_CHOICES)

            if payment_m not in valid:
                return Response(
                    {"error": f"Invalid payment method. Choose: {', '.join(valid)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if order.status != "pending":
                return Response(
                    {"error": "Can only change payment for pending orders"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order.payment_method = payment_m
            if payment_m == "COD":
                full_name = request.data.get("full_name", "").strip()
                phone = request.data.get("phone", "")
                if len(full_name.split()) < 3:
                    return Response({"error": "Full name must contain at least three words"}, status=400)
                if not phone.isdigit() or len(phone) < 7:
                    return Response({"error": "Valid phone number required"}, status=400)
                order.full_name = full_name
                order.phone = phone
                order.status = 'confirmed'
            order.save(update_fields=["payment_method", "status", "full_name", "phone"])

        serializer = OrderSerializer(order)
        return Response(serializer.data)
    


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request):
        if not request.user.is_email_verified:
           raise PermissionDenied("Please verify your email before checkout")
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.all()

        if not cart_items.exists():
            return Response(
                {"error": "cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


     
        total_price = sum(item.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            shipping_address=serializer.validated_data["shipping_address"],
            phone=serializer.validated_data["phone"],
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.price,
            )
            product = Product.objects.select_for_update().get(pk=cart_item.product.pk)
            product.stock -= cart_item.quantity
            product.save()

        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(
            Order.objects.select_for_update(), id=order_id, user=request.user
        )

        if order.status != "pending":
            return Response(
                {"error": "can not cancel the order after confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "cancelled"
        order.save()

        for item in order.items.all():
            if item.product:
                product = Product.objects.select_for_update().get(pk=item.product.pk)
                product.stock += item.quantity
                product.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data)



class AdminOrderListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderSerializer

    def get_queryset(self):
        archived = self.request.query_params.get("archived", "false").lower() == "true"
        qs = Order.objects.select_related('user').prefetch_related('items')
        if archived:
            return qs.filter(is_archived=True).order_by("-created_at")
        return qs.filter(is_archived=False).order_by("-created_at")
    
    
class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        serializer = AdminOrderSerializer(order)
        return Response(serializer.data)

    @transaction.atomic
    def patch(self, request, order_id):
        order = get_object_or_404(
            Order.objects.select_for_update(), id=order_id
        )
        serializer = AdminOrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            old_status = order.status
            serializer.save()
            if serializer.validated_data.get("status") == "cancelled" and old_status != "cancelled":
                for item in order.items.all():
                    if item.product:
                        product = Product.objects.select_for_update().get(pk=item.product.pk)
                        product.stock += item.quantity
                        product.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)