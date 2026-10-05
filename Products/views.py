from django.shortcuts import render, get_object_or_404
from Products.models import Product


def get_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product/product.html', context={'product': product})
