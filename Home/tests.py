from django.test import TestCase
from django.urls import reverse

from Products.models import Category, Product


class HomeTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            category_name="Electronics"
        )

        self.product = Product.objects.create(
            product_name="Test Phone",
            category=self.category,
            price=25000,
            stock=5,
            product_desription="Test product",
        )

    def test_home_page(self):
        response = self.client.get(
            reverse("index")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Test Phone"
        )

    def test_category_page(self):
        response = self.client.get(
            reverse(
                "category",
                kwargs={"category_slug": self.category.slug}
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Test Phone"
        )

    def test_invalid_category_returns_404(self):
        response = self.client.get(
            reverse(
                "category",
                kwargs={"category_slug": "invalid-category"}
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )