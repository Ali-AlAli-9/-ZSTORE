from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import Product
from .models import Order

User = get_user_model()


class CheckoutTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(
            name="Phone", price=500, stock=10
        )
        self.client.post("/cart/", {"product": self.product.id, "quantity": 2})

    def test_checkout_success_creates_order(self):
        response = self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(Order.objects.count(), 1)

    def test_checkout_returns_order_details(self):
        response = self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.assertEqual(response.data["total_price"], "1000.00")
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(len(response.data["items"]), 1)

    def test_checkout_empty_cart_fails(self):
        # Clear cart first
        self.client.post("/orders/checkout/",
                         {"shipping_address":  "123 Main St, Cairo", "phone": "0123456789"})
        response = self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_decrements_stock(self):
        self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)  # 10 - 2

    def test_checkout_clears_cart(self):
        self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        cart_response = self.client.get("/cart/")
        self.assertEqual(len(cart_response.data["items"]), 0)

    def test_checkout_without_address_fails(self):
        response = self.client.post(
            "/orders/checkout/", {"phone": "0123456789"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_without_phone_fails(self):
        response = self.client.post(
            "/orders/checkout/", {"shipping_address": "123 Main Street, Cairo"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_with_quantity_over_stock_succeeds_and_goes_negative(self):
        self.product.stock = 1
        self.product.save()
        response = self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, -1)


class CancelOrderTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(name="Phone", price=500, stock=10)
        self.client.post("/cart/", {"product": self.product.id, "quantity": 2})
        self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.order = Order.objects.first()

    def test_cancel_pending_order_success(self):
        response = self.client.post(f"/orders/{self.order.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_cancel_restores_stock(self):
        self.client.post(f"/orders/{self.order.id}/cancel/")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_cancel_confirmed_order_fails(self):
        self.order.status = "confirmed"
        self.order.save()
        response = self.client.post(f"/orders/{self.order.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_other_users_order_fails(self):
        other = User.objects.create_user(username="other", password="pass")
        self.client.force_authenticate(user=other)
        response = self.client.post(f"/orders/{self.order.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderPaymentTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="pass")
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(name="Phone", price=500, stock=10)
        self.client.post("/cart/", {"product": self.product.id, "quantity": 1})
        self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.order = Order.objects.first()

    def test_set_cod_with_valid_data_sets_confirmed(self):
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed Mohamed Ali", "phone": "0912345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_method, "COD")
        self.assertEqual(self.order.status, "confirmed")
        self.assertEqual(self.order.full_name, "Ahmed Mohamed Ali")
        self.assertEqual(self.order.phone, "0912345678")

    def test_set_cod_without_full_name_fails(self):
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "phone": "0912345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_cod_with_short_full_name_fails(self):
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed", "phone": "0912345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_cod_with_invalid_phone_fails(self):
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed Mohamed Ali", "phone": "abc"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_cod_with_short_phone_fails(self):
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed Mohamed Ali", "phone": "123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_invalid_payment_method_fails(self):
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "BITCOIN"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_payment_on_confirmed_order_fails(self):
        self.order.status = "confirmed"
        self.order.save()
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed Mohamed Ali", "phone": "0912345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_set_payment(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed Mohamed Ali", "phone": "0912345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_set_payment_for_other_users_order(self):
        other = User.objects.create_user(username="other", password="pass")
        self.client.force_authenticate(user=other)
        response = self.client.patch(
            f"/orders/{self.order.id}/",
            {"payment_method": "COD", "full_name": "Ahmed Mohamed Ali", "phone": "0912345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderListTest(APITestCase):
    def test_user_sees_only_own_orders(self):
        user1 = User.objects.create_user(username="user1", password="pass")
        user1.is_email_verified = True
        user1.save()
        user2 = User.objects.create_user(username="user2", password="pass")
        user2.is_email_verified = True
        user2.save()

        product = Product.objects.create(name="Test", price=100, stock=5)

        self.client.force_authenticate(user=user1)
        self.client.post("/cart/", {"product": product.id, "quantity": 1})
        self.client.post(
            "/orders/checkout/",
            {"shipping_address": "Addr 1", "phone": "0123456789"},
        )

        self.client.force_authenticate(user=user2)
        self.client.post("/cart/", {"product": product.id, "quantity": 1})
        self.client.post(
            "/orders/checkout/",
            {"shipping_address": "Addr 2", "phone": "0123456789"},
        )

        self.client.force_authenticate(user=user1)
        response = self.client.get("/orders/")
        orders = response.data.get("results", response.data)
        for order in orders:
            self.assertEqual(order["user"], user1.id)

    def test_unauthenticated_cannot_list_orders(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminOrderListTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="pass")
        self.user = User.objects.create_user(username="buyer", password="pass")
        self.user.is_email_verified = True
        self.user.save()
        self.product = Product.objects.create(name="Phone", price=500, stock=10)
        self.client.force_authenticate(user=self.user)
        self.client.post("/cart/", {"product": self.product.id, "quantity": 1})
        resp = self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.order_id = resp.data["id"]

    def test_unauthenticated_gets_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/orders/admin-orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_gets_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/orders/admin-orders/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_200(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/orders/admin-orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_sees_only_active_by_default(self):
        self.order = Order.objects.get(id=self.order_id)
        self.order.is_archived = True
        self.order.save()
        Order.objects.create(
            user=self.user, total_price=100, shipping_address="Addr", phone="0123456788"
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/orders/admin-orders/")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["is_archived"])

    def test_admin_archived_filter(self):
        self.order = Order.objects.get(id=self.order_id)
        self.order.is_archived = True
        self.order.save()
        Order.objects.create(
            user=self.user, total_price=100, shipping_address="Addr", phone="0123456788"
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/orders/admin-orders/?archived=true")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["is_archived"])

    def test_admin_detail_includes_username(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/orders/admin-orders/{self.order_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("username", response.data)
        self.assertEqual(response.data["username"], "buyer")


class AdminOrderPatchTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="pass")
        self.user = User.objects.create_user(username="buyer", password="pass")
        self.user.is_email_verified = True
        self.user.save()
        self.product = Product.objects.create(name="Phone", price=500, stock=10)
        self.client.force_authenticate(user=self.user)
        self.client.post("/cart/", {"product": self.product.id, "quantity": 1})
        resp = self.client.post(
            "/orders/checkout/",
            {"shipping_address": "123 Main Street, Cairo", "phone": "0123456789"},
        )
        self.order_id = resp.data["id"]

    def test_unauthenticated_gets_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"status": "shipped"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_gets_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"status": "shipped"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_change_status_to_confirmed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"status": "confirmed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "confirmed")

    def test_admin_can_change_status_to_shipped(self):
        order = Order.objects.get(id=self.order_id)
        order.status = "confirmed"
        order.save()
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"status": "shipped"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "shipped")

    def test_admin_can_change_status_to_delivered(self):
        order = Order.objects.get(id=self.order_id)
        order.status = "shipped"
        order.save()
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"status": "delivered"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "delivered")

    def test_admin_can_archive_order(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"is_archived": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_archived"])

    def test_invalid_status_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"status": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_payment_method_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/orders/admin-orders/{self.order_id}/", {"payment_method": "BITCOIN"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_patch_nonexistent_order(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/orders/admin-orders/999/", {"status": "shipped"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
