from django.db import models
from django.utils.text import slugify

# Create your models here.

class Category(models.Model):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True , null=True , blank=True)
    category_image = models.ImageField(upload_to="catgories")


    def save(self , *args , **kwargs):
        self.slug = slugify(self.category_name)
        super(Category ,self).save(*args , **kwargs)


    def __str__(self) -> str:
        return self.category_name


class ColorVariant(models.Model):
    color_name = models.CharField(max_length=100)
    price = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.color_name


class SizeVariant(models.Model):
    size_name = models.CharField(max_length=100)
    price = models.PositiveIntegerField(default=0)
    
    def __str__(self) -> str:
        return self.size_name


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)

    product_desription = models.TextField()

    color_variant = models.ManyToManyField(ColorVariant, blank=True)
    size_variant = models.ManyToManyField(SizeVariant, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.product_name

class ProductImage(models.Model):
    product = models.ForeignKey(Product , on_delete=models.CASCADE , related_name="product_images")
    image =  models.ImageField(upload_to="product")