from .models import Cart


def get_or_create_cart(request):
    """
    Returns the Cart for the logged-in user, or for the current
    anonymous session (creating the session if needed).
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(
        session_key=session_key, user=None
    )
    return cart


def merge_session_cart_into_user_cart(request, user, session_key=None):
    session_key = session_key or request.session.session_key
    if not session_key:
        return
    try:
        session_cart = Cart.objects.get(session_key=session_key, user=None)
    except Cart.DoesNotExist:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for item in session_cart.items.all():
        existing = user_cart.items.filter(
            product=item.product,
            color_variant=item.color_variant,
            size_variant=item.size_variant,
        ).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()

    session_cart.delete()
