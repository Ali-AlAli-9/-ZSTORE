from django.db import models
from django.conf import settings
from products.models import Product

User = settings.AUTH_USER_MODEL


# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ]
    
    PAYMENT_METHOD_CHOICES=[
        ("COD","cash on delivery"),
        ("CARD","card/online payment"),
    ]
    
    PAYMENT_STATUS_CHOICES=[
        ("pending","pending"),
        ("paid","paid"),
        ("failed","failed")
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=20)
    payment_method=models.CharField(max_length=20,choices=PAYMENT_METHOD_CHOICES,default="COD")
    payment_status=models.CharField(max_length=20,choices=PAYMENT_STATUS_CHOICES,default="pending")
    full_name = models.CharField(max_length=150, blank=True)
    is_archived = models.BooleanField(default=False)
    class Meta:
     indexes = [
        models.Index(
            fields=["-created_at"],
            name="idx_active_orders",
            condition=models.Q(is_archived=False)
        )
        ]
    VALID_TRANSITIONS = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["shipped", "cancelled"],
        "shipped": ["delivered"],
        "delivered": [],
        "cancelled": [],
    }

    def clean(self):
        if self.pk:
            try:
                old = Order.objects.get(pk=self.pk)
            except Order.DoesNotExist:
                return
            if self.status != old.status:
                valid_next = self.VALID_TRANSITIONS.get(old.status, [])
                if self.status not in valid_next:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        f"Cannot change status from '{old.status}' to '{self.status}'. "
                        f"Allowed transitions: {', '.join(valid_next) if valid_next else 'none'}"
                    )

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} * {self.quantity}" if self.product else "Deleted"
