from django.urls import path
from Orders.views import checkout, order_success, order_list

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('success/<int:order_id>/', order_success, name='order_success'),
    path('my-orders/', order_list, name='order_list'),
]
