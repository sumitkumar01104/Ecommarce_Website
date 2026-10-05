from django.db import models
from django.contrib.auth.models import User
from Products.models import Product


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    # Only Cash on Delivery is supported for now.
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='COD')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')

    total_amount = models.PositiveIntegerField(default=0)

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} ({self.user})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)

    # snapshot fields so the invoice stays correct even if the product changes later
    product_name = models.CharField(max_length=150)
    variant_info = models.CharField(max_length=150, blank=True)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    @property
    def sub_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
