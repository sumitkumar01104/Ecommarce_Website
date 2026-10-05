from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView

from Account.views import VerifiedTokenObtainPairView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Account
    path('account/', include('Account.urls')),
    path('account/', include('verificationsystem.urls')),

    # Website
    path('', include('Home.urls')),

    # Products
    path('product/', include('Products.urls')),

    # Cart
    path('cart/', include('Cart.urls')),

    # Orders
    path('orders/', include('Orders.urls')),

    # JWT Authentication
    path(
        'api/token/',
        VerifiedTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    # API Schema
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),

    # Swagger
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    # ReDoc
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]

