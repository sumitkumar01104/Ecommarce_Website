from django.shortcuts import render, get_object_or_404
from Products.models import Product, Category


def index(request, category_slug=None):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category)
    else:
        category = None
        products = Product.objects.all()

    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(product_name__icontains=q)

    context = {'products': products, 'category': category, 'q': q}
    return render(request, 'home/index.html', context)