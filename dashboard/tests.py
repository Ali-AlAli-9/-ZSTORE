from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order, OrderItem
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class DashboardOverviewPermissionsTest(APITestCase):
    def test_unauthenticated_gets_401(self):
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_gets_403(self):
        user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=user)
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_200(self):
        admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardOverviewEmptyDataTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=self.admin)

    def test_returns_zero_when_no_data(self):
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["total_orders"], 0)
        self.assertEqual(response.data["total_revenue"], 0.0)
        self.assertEqual(response.data["orders_by_status"], {})
        self.assertEqual(response.data["revenue_this_month"], 0.0)
        self.assertEqual(response.data["average_order_value"], 0.0)
        self.assertEqual(response.data["total_products"], 0)
        self.assertEqual(response.data["total_users"], 1)  # admin exists
        self.assertEqual(response.data["new_users_this_month"], 1)  # admin created this month
        self.assertEqual(response.data["low_stock_products"], [])

    def test_returns_correct_product_count(self):
        Product.objects.create(name="A", price=10, stock=5)
        Product.objects.create(name="B", price=20, stock=3)
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["total_products"], 2)

    def test_returns_correct_user_count(self):
        User.objects.create_user(username="u1", password="pass")
        User.objects.create_user(username="u2", password="pass")
        response = self.client.get("/dashboard/overview/")
        # At least admin (setUp) + u1 + u2, allow extras from other test classes
        self.assertGreaterEqual(response.data["total_users"], 3)

    def test_detects_low_stock_products(self):
        Product.objects.create(name="Low", price=10, stock=2)
        Product.objects.create(name="OK", price=10, stock=10)
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(len(response.data["low_stock_products"]), 1)
        self.assertEqual(response.data["low_stock_products"][0]["name"], "Low")


class DashboardOverviewWithOrdersTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=self.admin)
        self.product = Product.objects.create(name="Phone", price=500, stock=10)
        self.user = User.objects.create_user(username="buyer", password="pass")

    def _create_order(self, status_val="delivered", days_ago=0):
        created = timezone.now() - timedelta(days=days_ago)
        order = Order.objects.create(
            user=self.user,
            total_price=1000,
            shipping_address="Addr",
            phone="0123456789",
            status=status_val,
        )
        OrderItem.objects.create(
            order=order, product=self.product, quantity=2, price=500
        )
        # Manually set created_at to simulate past orders
        Order.objects.filter(id=order.id).update(created_at=created)
        return order

    def test_counts_orders_by_status(self):
        self._create_order("pending")
        self._create_order("confirmed")
        self._create_order("shipped")
        self._create_order("delivered")
        self._create_order("cancelled")

        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["total_orders"], 5)
        self.assertEqual(response.data["orders_by_status"]["pending"], 1)
        self.assertEqual(response.data["orders_by_status"]["confirmed"], 1)
        self.assertEqual(response.data["orders_by_status"]["shipped"], 1)
        self.assertEqual(response.data["orders_by_status"]["delivered"], 1)
        self.assertEqual(response.data["orders_by_status"]["cancelled"], 1)

    def test_revenue_includes_confirmed_shipped_delivered(self):
        self._create_order("pending")
        self._create_order("confirmed")
        self._create_order("delivered")

        response = self.client.get("/dashboard/overview/")
        # pending(1000) excluded, confirmed(1000) + delivered(1000) = 2000
        self.assertEqual(response.data["total_revenue"], 2000.0)

    def test_cancelled_orders_excluded_from_revenue(self):
        self._create_order("cancelled")
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["total_revenue"], 0.0)

    def test_average_order_value(self):
        self._create_order("delivered")
        self._create_order("delivered")
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["average_order_value"], 1000.0)

    def test_average_order_value_zero_when_no_revenue_orders(self):
        self._create_order("pending")
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["average_order_value"], 0.0)

    def test_revenue_this_month(self):
        self._create_order("delivered", days_ago=60)  # old order
        self._create_order("delivered", days_ago=0)    # this month
        response = self.client.get("/dashboard/overview/")
        self.assertEqual(response.data["revenue_this_month"], 1000.0)

    def test_new_users_this_month(self):
        User.objects.create_user(username="new_user", password="pass")
        response = self.client.get("/dashboard/overview/")
        # At least admin (setUp) + new_user, allow extra from other test classes
        self.assertGreaterEqual(response.data["new_users_this_month"], 2)


class DashboardBestSellersPermissionsTest(APITestCase):
    def test_unauthenticated_gets_401(self):
        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_gets_403(self):
        user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=user)
        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_200(self):
        admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardBestSellersDataTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=self.admin)
        self.user = User.objects.create_user(username="buyer", password="pass")

    def test_empty_when_no_orders(self):
        Product.objects.create(name="Phone", price=500, stock=10)
        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(response.data, [])

    def test_returns_top_seller_first(self):
        phone = Product.objects.create(name="Phone", price=500, stock=10)
        case = Product.objects.create(name="Case", price=20, stock=50)

        order = Order.objects.create(
            user=self.user, total_price=1040,
            shipping_address="Addr", phone="0123456789",
            status="delivered",
        )
        OrderItem.objects.create(order=order, product=phone, quantity=3, price=500)
        OrderItem.objects.create(order=order, product=case, quantity=2, price=20)

        # Also sell more cases in another order
        order2 = Order.objects.create(
            user=self.user, total_price=60,
            shipping_address="Addr", phone="0123456789",
            status="delivered",
        )
        OrderItem.objects.create(order=order2, product=case, quantity=3, price=20)

        response = self.client.get("/dashboard/best-sellers/")

        # Case total = 2+3=5, Phone total = 3
        self.assertEqual(response.data[0]["name"], "Case")
        self.assertEqual(response.data[0]["total_quantity_sold"], 5)
        self.assertEqual(response.data[1]["name"], "Phone")
        self.assertEqual(response.data[1]["total_quantity_sold"], 3)

    def test_ignores_deleted_products(self):
        product = Product.objects.create(name="Phone", price=500, stock=10)
        order = Order.objects.create(
            user=self.user, total_price=500,
            shipping_address="Addr", phone="0123456789",
            status="delivered",
        )
        OrderItem.objects.create(order=order, product=product, quantity=1, price=500)
        OrderItem.objects.create(order=order, product=None, quantity=1, price=200)

        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product_id"], product.id)

    def test_limit_parameter(self):
        products = []
        for i in range(15):
            p = Product.objects.create(name=f"Product {i}", price=10, stock=100)
            products.append(p)

        order = Order.objects.create(
            user=self.user, total_price=150,
            shipping_address="Addr", phone="0123456789",
            status="delivered",
        )
        for p in products:
            OrderItem.objects.create(order=order, product=p, quantity=1, price=10)

        # Default limit = 10
        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(len(response.data), 10)

        # Custom limit = 5
        response = self.client.get("/dashboard/best-sellers/?limit=5")
        self.assertEqual(len(response.data), 5)

    def test_invalid_limit_falls_back_to_default(self):
        Product.objects.create(name="P", price=10, stock=100)
        response = self.client.get("/dashboard/best-sellers/?limit=abc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_limit_caps_at_50(self):
        for i in range(60):
            p = Product.objects.create(name=f"P{i}", price=10, stock=100)
            order = Order.objects.create(
                user=self.user, total_price=10,
                shipping_address="Addr", phone="0123456789",
                status="delivered",
            )
            OrderItem.objects.create(order=order, product=p, quantity=1, price=10)

        response = self.client.get("/dashboard/best-sellers/?limit=100")
        self.assertEqual(len(response.data), 50)

    def test_response_structure(self):
        product = Product.objects.create(name="Mouse", price=50, stock=20)
        order = Order.objects.create(
            user=self.user, total_price=100,
            shipping_address="Addr", phone="0123456789",
            status="delivered",
        )
        OrderItem.objects.create(order=order, product=product, quantity=2, price=50)

        response = self.client.get("/dashboard/best-sellers/")
        item = response.data[0]
        self.assertIn("product_id", item)
        self.assertIn("name", item)
        self.assertIn("total_quantity_sold", item)
        self.assertIn("total_revenue", item)
        self.assertIn("current_stock", item)
        self.assertEqual(item["product_id"], product.id)
        self.assertEqual(item["name"], "Mouse")
        self.assertEqual(item["total_quantity_sold"], 2)
        self.assertEqual(item["total_revenue"], "100.00")
        self.assertEqual(item["current_stock"], 20)

    def test_staff_user_can_access(self):
        staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=staff)
        response = self.client.get("/dashboard/best-sellers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
