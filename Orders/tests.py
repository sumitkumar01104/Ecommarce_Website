from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch

from Account.models import Profile
from Products.models import Category, Product, SizeVariant
from Cart.models import Cart, CartItem
from Orders.models import Order, OrderItem


class OrderTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="Test@12345"
        )

        # Profile is automatically created by signal
        self.profile = Profile.objects.get(user=self.user)

        self.profile.first_name = "Test"
        self.profile.last_name = "User"
        self.profile.is_email_verified = True
        self.profile.save(
            update_fields=[
                "first_name",
                "last_name",
                "is_email_verified",
            ]
        )

        self.category = Category.objects.create(
            category_name="Electronics"
        )

        self.product = Product.objects.create(
            product_name="Test Laptop",
            category=self.category,
            price=50000,
            stock=10,
            product_desription="Test laptop",
        )

        self.client.force_login(self.user)

        self.cart = Cart.objects.create(
            user=self.user
        )

        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
        )

    def checkout_data(self):
        return {
            "full_name": "Test User",
            "phone_number": "9876543210",
            "address_line": "123 Test Street",
            "city": "Aligarh",
            "state": "Uttar Pradesh",
            "pincode": "202001",
        }

    def test_checkout_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("checkout")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_empty_cart_redirects(self):
        self.cart.items.all().delete()

        response = self.client.get(
            reverse("checkout")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_invalid_phone_rejected(self):
        response = self.client.post(
            reverse("checkout"),
            {
                **self.checkout_data(),
                "phone_number": "1234567890",
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            Order.objects.count(),
            0
        )

    def test_invalid_pincode_rejected(self):
        response = self.client.post(
            reverse("checkout"),
            {
                **self.checkout_data(),
                "pincode": "12345",
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            Order.objects.count(),
            0
        )

    @patch("Orders.views.send_order_confirmation_email.delay")
    def test_successful_checkout(self, mock_email):
        response = self.client.post(
            reverse("checkout"),
            self.checkout_data()
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            Order.objects.count(),
            1
        )

        order = Order.objects.first()

        self.assertEqual(
            order.user,
            self.user
        )

        self.assertEqual(
            order.total_amount,
            100000
        )

        self.assertEqual(
            order.items.count(),
            1
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            8
        )

        self.cart.refresh_from_db()

        self.assertEqual(
            self.cart.items.count(),
            0
        )

        mock_email.assert_called_once_with(
            order.id
        )

    @patch("Orders.views.send_order_confirmation_email.delay")
    def test_order_item_snapshot(self, mock_email):
        self.client.post(
            reverse("checkout"),
            self.checkout_data()
        )

        order_item = OrderItem.objects.first()

        self.assertEqual(
            order_item.product_name,
            "Test Laptop"
        )

        self.assertEqual(
            order_item.unit_price,
            50000
        )

        self.assertEqual(
            order_item.quantity,
            2
        )

    def test_insufficient_stock_rejected(self):
        self.product.stock = 1
        self.product.save()

        response = self.client.post(
            reverse("checkout"),
            self.checkout_data()
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            Order.objects.count(),
            0
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            1
        )

    @patch("Orders.views.send_order_confirmation_email.delay")
    def test_user_can_view_own_order(self, mock_email):
        self.client.post(
            reverse("checkout"),
            self.checkout_data()
        )

        order = Order.objects.first()

        response = self.client.get(
            reverse(
                "order_success",
                kwargs={
                    "order_id": order.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_user_cannot_view_other_users_order(self):
        other_user = User.objects.create_user(
            username="other@example.com",
            password="Test@12345"
        )

        order = Order.objects.create(
            user=other_user,
            full_name="Other User",
            phone_number="9876543210",
            address_line="Other Address",
            city="Aligarh",
            state="Uttar Pradesh",
            pincode="202001",
            payment_method="COD",
            total_amount=1000,
        )

        response = self.client.get(
            reverse(
                "order_success",
                kwargs={
                    "order_id": order.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_order_list_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("order_list")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_same_product_two_variants_exceeding_stock_rejected(self):
        size_m = SizeVariant.objects.create(size_name="M")
        size_l = SizeVariant.objects.create(size_name="L")

        self.cart.items.all().delete()
        self.product.stock = 5
        self.product.save()

        CartItem.objects.create(cart=self.cart, product=self.product,
                                size_variant=size_m, quantity=4)
        CartItem.objects.create(cart=self.cart, product=self.product,
                                size_variant=size_l, quantity=4)

        response = self.client.post(reverse("checkout"), self.checkout_data())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)