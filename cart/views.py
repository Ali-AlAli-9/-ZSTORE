from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Cart,CartItem
from products.models import Product
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import CartItemSerializer
from django.db import transaction

# Create your views here.

class CartView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        cart,creatd=Cart.objects.get_or_create(user=request.user)
        data={ 
              "cart_id":cart.id,
              "items" : [{
                  'product': item.product.name if item.product else '[Deleted]',
                  'quantity':item.quantity,
              }
              for item in cart.items.all()]      
        }

        return Response(data)
    
    @transaction.atomic
    def post(self,request):
        cart,created=Cart.objects.get_or_create(user=request.user)
        serializer=CartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
        product = Product.objects.select_for_update().get(pk=serializer.validated_data["product"].pk)
        quantity=serializer.validated_data["quantity"]
        
        item,created=CartItem.objects.get_or_create(cart=cart,product=product)
        if created:
           item.price = product.price
        if quantity == 0:
            item.delete()
            return Response({"message":"removed from cart"})
        
        item.quantity=quantity
        item.save()
        return Response({"message":"cart updated"})