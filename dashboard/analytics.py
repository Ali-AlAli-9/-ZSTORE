from django.db.models import Count, Sum, F
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product
from users.models import User


REVENUE_STATUSES = ["confirmed", "shipped", "delivered"]


def orders_by_status():
    return dict(
        Order.objects.values_list("status").annotate(count=Count("id")).order_by("status")
    )
    
    
    
def total_orders():
    return Order.objects.count()

def total_revenue():
    result=Order.objects.filter(
        status__in=REVENUE_STATUSES
    ).aggregate(total=Sum("total_price"))
    return float(result["total"] or 0)

def revenue_this_month():
    now=timezone.now()
    start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    result=Order.objects.filter(status__in=REVENUE_STATUSES,created_at__gte=start,).aggregate(total=Sum("total_price"))
    return float(result["total"] or 0)

def average_order_value():
    count = Order.objects.filter(status__in=REVENUE_STATUSES).count()
    if count == 0:
        return 0.0
    total = total_revenue()
    return round(total / count, 2)

def best_sellers(limit=10):
    return list(
        OrderItem.objects.filter(
            product__isnull=False,
            order__status__in=REVENUE_STATUSES,
        )
        .values(pid=F("product__id"), name=F("product__name"), stock=F("product__stock"))
        .annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum(F("price") * F("quantity")),
        )
        .order_by("-total_quantity")[:limit]
    )
    
    
def low_stock_products(threshold=5):
    return list(
        Product.objects.filter(stock__lte=threshold)
        .values("id", "name", "stock")
        .order_by("stock")
    )
    
    
def total_products():
    return Product.objects.count()

def total_users():
    return User.objects.count()

def new_users_this_month():
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return User.objects.filter(date_joined__gte=start).count()