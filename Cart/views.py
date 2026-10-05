from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from Products.models import Product, ColorVariant, SizeVariant
from .models import CartItem
from .utils import get_or_create_cart


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _parse_quantity(request, default=1):
    """Safely read `quantity` from POST data. Returns None if it isn't a valid integer."""
    raw = request.POST.get('quantity', default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


@require_POST
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    cart = get_or_create_cart(request)

    quantity = _parse_quantity(request)
    if quantity is None:
        error = 'Please enter a valid quantity.'
        if _is_ajax(request):
            return JsonResponse({'success': False, 'message': error}, status=400)
        messages.error(request, error)
        return redirect('cart_detail')
    if quantity < 1:
        quantity = 1

    color_id = request.POST.get('color_variant')
    size_id = request.POST.get('size_variant')
    color_variant = (product.color_variant.filter(id=color_id).first()
                     if color_id and color_id.isdigit() else None)
    size_variant = (product.size_variant.filter(id=size_id).first()
                    if size_id and size_id.isdigit() else None)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        color_variant=color_variant,
        size_variant=size_variant,
        defaults={'quantity': quantity},
    )
    if not created:
        item.quantity += quantity
        item.save()

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': f'{product.product_name} added to cart.',
            'cart_total_items': cart.total_items,
            'cart_total_amount': cart.total_amount,
        })

    messages.success(request, f'{product.product_name} added to cart.')
    if request.POST.get('buy_now'):
        return redirect('checkout')
    return redirect('cart_detail')


def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product', 'color_variant', 'size_variant').all()
    return render(request, 'cart/cart.html', {
        'cart': cart,
        'items': items,
    })


@require_POST
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    quantity = _parse_quantity(request)
    if quantity is None:
        error = 'Please enter a valid quantity.'
        if _is_ajax(request):
            return JsonResponse({'success': False, 'message': error}, status=400)
        messages.error(request, error)
        return redirect('cart_detail')
    if quantity < 1:
        item.delete()
        messages.info(request, 'Item removed from cart.')
    else:
        item.quantity = quantity
        item.save()
        messages.success(request, 'Cart updated.')

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.total_items,
            'cart_total_amount': cart.total_amount,
        })
    return redirect('cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.total_items,
            'cart_total_amount': cart.total_amount,
        })
    messages.success(request, 'Item removed from cart.')
    return redirect('cart_detail')