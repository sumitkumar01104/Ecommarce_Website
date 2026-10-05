from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from Products.models import Category, Product, ColorVariant, SizeVariant
from .models import Cart, CartItem


class CartTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            category_name="Electronics"
        )

        self.product = Product.objects.create(
            product_name="Test Phone",
            category=self.category,
            price=1000,
            stock=10,
            product_desription="Test description",
        )

    def test_add_product_to_guest_cart(self):
        response = self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {
                "quantity": 2
            }
        )

        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(
            session_key=self.client.session.session_key
        )

        item = CartItem.objects.get(cart=cart)

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

    def test_add_product_increases_existing_quantity(self):
        self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {"quantity": 2}
        )

        self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {"quantity": 3}
        )

        cart = Cart.objects.get(
            session_key=self.client.session.session_key
        )

        item = CartItem.objects.get(cart=cart)

        self.assertEqual(item.quantity, 5)

    def test_update_cart_item(self):
        self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {"quantity": 2}
        )

        cart = Cart.objects.get(
            session_key=self.client.session.session_key
        )

        item = cart.items.first()

        response = self.client.post(
            reverse(
                "update_cart_item",
                kwargs={"item_id": item.id}
            ),
            {"quantity": 5}
        )

        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()

        self.assertEqual(item.quantity, 5)

    def test_remove_cart_item(self):
        self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {"quantity": 1}
        )

        cart = Cart.objects.get(
            session_key=self.client.session.session_key
        )

        item = cart.items.first()

        response = self.client.post(
            reverse(
                "remove_from_cart",
                kwargs={"item_id": item.id}
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            CartItem.objects.filter(id=item.id).exists()
        )

    def test_cart_total(self):
        self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {"quantity": 3}
        )

        cart = Cart.objects.get(
            session_key=self.client.session.session_key
        )

        self.assertEqual(cart.total_items, 3)
        self.assertEqual(cart.total_amount, 3000)

    def test_variant_price(self):
        color = ColorVariant.objects.create(
            color_name="Black",
            price=200
        )

        size = SizeVariant.objects.create(
            size_name="Large",
            price=300
        )

        self.product.color_variant.add(color)
        self.product.size_variant.add(size)

        cart = Cart.objects.create(
            session_key="test-session"
        )

        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            color_variant=color,
            size_variant=size,
            quantity=2,
        )

        self.assertEqual(item.unit_price, 1500)
        self.assertEqual(item.sub_total, 3000)

    def test_authenticated_user_gets_user_cart(self):
        user = User.objects.create_user(
            username="cartuser@example.com",
            password="Test@12345"
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("cart_detail")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Cart.objects.filter(user=user).exists()
        )

    def test_invalid_variant_id_does_not_crash(self):
        response = self.client.post(
            reverse(
                "add_to_cart",
                kwargs={"slug": self.product.slug}
            ),
            {
                "quantity": 1,
                "color_variant": "abc",
                "size_variant": "xyz",
            }
        )

        self.assertEqual(response.status_code, 302)

        item = CartItem.objects.get()
        self.assertIsNone(item.color_variant)
        self.assertIsNone(item.size_variant)