from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    register_page,
    login_page,
    logout_page,
)


urlpatterns = [
    # Template views
    path('register/', register_page, name='register'),
    path('login/', login_page, name='login'),
    path('logout/', logout_page, name='logout'),

    # REST API
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),

    # Current user's profile
    path(
        'api/profile/',
        ProfileView.as_view(),
        name='profile'
    ),
]