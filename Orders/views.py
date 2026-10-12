from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings
import re
from collections import defaultdict

from Products.models import Product
from Cart.utils import get_or_create_cart
from .models import Order, OrderItem
from .tasks import send_order_confirmation_email


PHONE_RE = re.compile(r'^[6-9]\d{9}$')
PINCODE_RE = re.compile(r'^\d{6}$')


@login_required(login_url='login')
def checkout(request):
    cart = get_or_create_cart(request)

    items = cart.items.select_related(
        'product',
        'color_variant',
        'size_variant'
    ).all()

    # Check empty cart
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect('cart_detail')

    # Handle checkout form submission
    if request.method == 'POST':

        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address_line = request.POST.get('address_line', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()

        # Required fields validation
        if not all([
            full_name,
            phone_number,
            address_line,
            city,
            state,
            pincode
        ]):
            messages.error(
                request,
                "Please fill in all delivery details."
            )

            return render(
                request,
                'orders/checkout.html',
                {
                    'cart': cart,
                    'items': items,
                    'delivery_days': settings.DELIVERY_DAYS
                }
            )

        # Phone number validation
        if not PHONE_RE.match(phone_number):
            messages.error(
                request,
                "Please enter a valid 10-digit mobile number "
                "(starting with 6-9)."
            )

            return render(
                request,
                'orders/checkout.html',
                {
                    'cart': cart,
                    'items': items,
                    'delivery_days': settings.DELIVERY_DAYS
                }
            )

        # Pincode validation
        if not PINCODE_RE.match(pincode):
            messages.error(
                request,
                "Please enter a valid 6-digit pincode."
            )

            return render(
                request,
                'orders/checkout.html',
                {
                    'cart': cart,
                    'items': items,
                    'delivery_days': settings.DELIVERY_DAYS
                }
            )

        # Create order and order items
        with transaction.atomic():

            # Lock the products (ordered by id to avoid deadlocks)
            product_ids = {item.product_id for item in items}
            locked = {
                p.id: p
                for p in Product.objects
                .select_for_update()
                .filter(id__in=product_ids)
                .order_by('id')
            }

            # Total quantity per product (all sizes/colours combined)
            needed = defaultdict(int)
            for item in items:
                needed[item.product_id] += item.quantity

            # Check stock on the locked, fresh rows
            for product_id, qty in needed.items():
                product = locked[product_id]

                if product.stock < qty:
                    messages.error(
                        request,
                        f"Sorry, only {product.stock} unit(s) of "
                        f"{product.product_name} are available."
                    )

                    return render(
                        request,
                        'orders/checkout.html',
                        {
                            'cart': cart,
                            'items': items,
                            'delivery_days': settings.DELIVERY_DAYS
                        }
                    )

            # Create order
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone_number,
                address_line=address_line,
                city=city,
                state=state,
                pincode=pincode,
                payment_method='COD',
                total_amount=cart.total_amount,
            )

            # Create order items and reduce stock
            for item in items:

                variant_parts = []

                if item.color_variant:
                    variant_parts.append(
                        item.color_variant.color_name
                    )

                if item.size_variant:
                    variant_parts.append(
                        item.size_variant.size_name
                    )

                # Create OrderItem
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.product_name,
                    variant_info=" / ".join(variant_parts),
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                )

                # Reduce product stock (on the locked object)
                locked_product = locked[item.product_id]
                locked_product.stock -= item.quantity
                locked_product.save(update_fields=['stock'])

            # Clear cart after order is created
            items.delete()

        # Send confirmation email asynchronously (skipped in demo mode,
        # where there is no Celery worker)
        if not settings.DEMO_MODE:
            try:
                send_order_confirmation_email.delay(order.id)

            except Exception:
                messages.warning(
                    request,
                    "Order placed, but the confirmation email could not "
                    "be queued. Please make sure Redis/Celery worker is running."
                )

        messages.success(
            request,
            f"Order {order.order_number} placed successfully!"
        )

        return redirect(
            'order_success',
            order_id=order.id
        )

    # GET request
    return render(
        request,
        'orders/checkout.html',
        {
            'cart': cart,
            'items': items,
            'delivery_days': settings.DELIVERY_DAYS
        }
    )


@login_required(login_url='login')
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        'orders/order_success.html',
        {
            'order': order,
            'demo_mode': settings.DEMO_MODE
        }
    )


@login_required(login_url='login')
def order_list(request):

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items')
        .order_by('-created_at')
    )

    return render(
        request,
        'orders/order_list.html',
        {
            'orders': orders
        }
    )
