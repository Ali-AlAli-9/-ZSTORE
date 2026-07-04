from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Product

User = get_user_model()


class ProductListTest(APITestCase):
    def test_anyone_can_list_products(self):
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anyone_can_retrieve_product(self):
        product = Product.objects.create(name="Phone", price=500, stock=10)
        response = self.client.get(f"/products/{product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_paginated_results(self):
        for i in range(25):
            Product.objects.create(name=f"Product {i}", price=10, stock=5)
        response = self.client.get("/products/")
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 20)


class ProductCreateTest(APITestCase):
    def test_unauthenticated_cannot_create(self):
        response = self.client.post("/products/", {"name": "Phone", "price": 500})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_cannot_create(self):
        user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=user)
        response = self.client.post("/products/", {"name": "Phone", "price": 500})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=admin)
        response = self.client.post(
            "/products/", {"name": "Phone","description": "Smartphone","price": 500, "stock": 10}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_negative_price_fails(self):
        admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=admin)
        response = self.client.post(
            "/products/", {"name": "Phone", "price": -5, "stock": 10}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", str(response.data))

    def test_create_with_negative_stock_fails(self):
        admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=admin)
        response = self.client.post(
            "/products/", {"name": "Phone", "price": 100, "stock": -1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stock", str(response.data))


class ProductSearchFilterTest(APITestCase):
    def setUp(self):
        Product.objects.create(name="iPhone 16", description="Apple phone", price=5000, stock=10)
        Product.objects.create(name="Samsung TV", description="LED TV", price=3000, stock=5)
        Product.objects.create(name="iPad", description="Apple tablet", price=4000, stock=8)

    def test_search_by_name(self):
        response = self.client.get("/products/?search=iphone")
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_by_description(self):
        response = self.client.get("/products/?search=tablet")
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_price_min(self):
        response = self.client.get("/products/?price__gte=4000")
        self.assertEqual(len(response.data["results"]), 2)

    def test_order_by_price_ascending(self):
        response = self.client.get("/products/?ordering=price")
        prices = [item["price"] for item in response.data["results"]]
        self.assertEqual(prices, sorted(prices))