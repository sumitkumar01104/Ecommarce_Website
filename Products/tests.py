from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, ColorVariant, SizeVariant


class ProductTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            category_name="Electronics"
        )

        self.product = Product.objects.create(
            product_name="Test Phone",
            category=self.category,
            price=25000,
            stock=10,
            product_desription="Test product description",
        )

    def test_category_created(self):
        self.assertEqual(
            self.category.category_name,
            "Electronics"
        )

    def test_category_slug_created(self):
        self.assertEqual(
            self.category.slug,
            "electronics"
        )

    def test_product_created(self):
        self.assertEqual(
            self.product.product_name,
            "Test Phone"
        )

    def test_product_slug_created(self):
        self.assertEqual(
            self.product.slug,
            "test-phone"
        )

    def test_product_detail_page(self):
        response = self.client.get(
            reverse(
                "get_product",
                kwargs={"slug": self.product.slug}
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_product_detail_invalid_slug(self):
        response = self.client.get(
            reverse(
                "get_product",
                kwargs={"slug": "does-not-exist"}
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_product_variants(self):
        color = ColorVariant.objects.create(
            color_name="Black",
            price=500
        )

        size = SizeVariant.objects.create(
            size_name="Large",
            price=1000
        )

        self.product.color_variant.add(color)
        self.product.size_variant.add(size)

        self.assertIn(
            color,
            self.product.color_variant.all()
        )

        self.assertIn(
            size,
            self.product.size_variant.all()
        )