from django.urls import path
from Home.views import index

urlpatterns = [
    path('', index, name='index'),
    path('category/<slug:category_slug>/', index, name='category'),
]
