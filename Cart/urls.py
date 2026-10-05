from django.urls import path
from Cart.views import add_to_cart, cart_detail, update_cart_item, remove_from_cart

urlpatterns = [
    path('', cart_detail, name='cart_detail'),
    path('add/<slug:slug>/', add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
]
