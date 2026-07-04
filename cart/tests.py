from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()


class CartAddTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(
            name="Phone", price=500, stock=10
        )

    def test_add_to_cart_success(self):
        response = self.client.post(
            "/cart/", {"product": self.product.id, "quantity": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_more_than_stock_succeeds(self):
        response = self.client.post(
            "/cart/", {"product": self.product.id, "quantity": 20}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_remove_item_from_cart(self):
        self.client.post("/cart/", {"product": self.product.id, "quantity": 2})
        response = self.client.post(
            "/cart/", {"product": self.product.id, "quantity": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_response = self.client.get("/cart/")
        self.assertEqual(len(cart_response.data["items"]), 0)

    def test_unauthenticated_cannot_add(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/cart/", {"product": self.product.id, "quantity": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_product_sets_quantity(self):
        self.client.post("/cart/", {"product": self.product.id, "quantity": 2})
        response = self.client.post(
            "/cart/", {"product": self.product.id, "quantity": 3}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Quantity is SET to 3 (not added)
        cart_response = self.client.get("/cart/")
        self.assertEqual(cart_response.data["items"][0]["quantity"], 3)


class CartGetTest(APITestCase):
    def test_get_cart_returns_items(self):
        user = User.objects.create_user(username="user2", password="pass")
        self.client.force_authenticate(user=user)
        product = Product.objects.create(name="TV", price=2000, stock=5)
        self.client.post("/cart/", {"product": product.id, "quantity": 1})
        response = self.client.get("/cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertEqual(len(response.data["items"]), 1)