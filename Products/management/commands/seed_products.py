import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from Products.models import Category, Product, ProductImage


CATEGORY_DATA = [
    ("Men's Fashion", "catgories/1.jpg"),
    ("Women's Fashion", "catgories/images.jfif"),
    ("Electronics", "catgories/images_aQdeqpm.jfif"),
    ("Footwear", "catgories/1.jpg"),
    ("Accessories", "catgories/images.jfif"),
]

PRODUCT_DATA = [
    ("Men's Fashion", "Classic Denim Jacket", 1999, "images/items/1.jpg"),
    ("Men's Fashion", "Slim Fit Chinos", 1299, "images/items/2.jpg"),
    ("Women's Fashion", "Floral Summer Dress", 1599, "images/items/3.jpg"),
    ("Electronics", "Wireless Bluetooth Headphones", 2499, "images/items/4.jpg"),
    ("Electronics", "Smart Fitness Band", 1799, "images/items/comp.png"),
    ("Footwear", "Running Sports Shoes", 2199, "images/items/5.jpg"),
    ("Accessories", "Leather Wallet", 899, "images/items/6.jpg"),
]


class Command(BaseCommand):
    help = "Sample categories, products aur unki images seed karta hai (agar pehle se nahi hain)"

    def handle(self, *args, **options):
        static_dir = settings.STATICFILES_DIRS[0]

        categories = {}
        for name, img_rel_path in CATEGORY_DATA:
            category, created = Category.objects.get_or_create(category_name=name)
            if created:
                src = os.path.join(static_dir, img_rel_path)
                if os.path.exists(src):
                    with open(src, "rb") as f:
                        category.category_image.save(os.path.basename(src), File(f), save=True)
                self.stdout.write(self.style.SUCCESS(f"Category banayi: {name}"))
            else:
                self.stdout.write(f"Category pehle se maujood: {name}")
            categories[name] = category

        for cat_name, prod_name, price, img_rel_path in PRODUCT_DATA:
            category = categories[cat_name]
            product, created = Product.objects.get_or_create(
                product_name=prod_name,
                defaults={
                    "category": category,
                    "price": price,
                    "product_desription": f"High quality {prod_name} from our {cat_name} collection.",
                },
            )

            if not product.product_images.exists():
                src = os.path.join(static_dir, img_rel_path)
                if os.path.exists(src):
                    with open(src, "rb") as f:
                        product_image = ProductImage(product=product)
                        product_image.image.save(os.path.basename(src), File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Product + image banayi: {prod_name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Sample image nahi mili: {src}"))
            else:
                self.stdout.write(f"Product pehle se maujood: {prod_name}")

        self.stdout.write(self.style.SUCCESS("Seeding complete! Ab home page reload karo."))
