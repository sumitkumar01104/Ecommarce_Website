from django.urls import path
from verificationsystem.views import activate_account

urlpatterns = [
    path('activate/<str:email_token>/', activate_account, name='activate_account'),
]