from django.db import models
from django.contrib.auth.models import User
from Products.models import Product, ColorVariant, SizeVariant


class Cart(models.Model):
    """One cart per logged-in user, or per anonymous session."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart'
    )
    session_key = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.pk} ({self.user or self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        return sum(item.sub_total for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size_variant = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'color_variant', 'size_variant')

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"

    @property
    def unit_price(self):
        price = self.product.price
        if self.color_variant:
            price += self.color_variant.price
        if self.size_variant:
            price += self.size_variant.price
        return price

    @property
    def sub_total(self):
        return self.unit_price * self.quantity
