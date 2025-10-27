from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Category(models.Model):
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        indexes = [models.Index(fields=["name"]),]

    name = models.CharField("Categoría", max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_categories", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_categories", verbose_name="Modificado por")

    def __str__(self):
        return self.name
    
    #TODO: deactivate category products when setting the category is_active to False
    #TODO: Category get_absolute_url


class Product(models.Model):
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["name"]),
        ]

    class ProductType(models.TextChoices):
        EQUIPO = "EQU", "Equipo"
        CONSUMIBLE = "CON", "Consumible"
        SERVICIO = "SER", "Servicio"
        ACCESORIO = "ACC", "Accesorio"
        REFACCIONES = "REF", "Refacciones"

    sku = models.CharField("Número de parte", max_length=10, unique=True)
    name = models.CharField("Producto", max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField("Descripción", blank=True)
    price = models.DecimalField("Precio", max_digits=12, decimal_places=2)
    product_type = models.CharField("Tipo de producto", max_length=3, choices=ProductType.choices, default=ProductType.CONSUMIBLE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    related_product = models.ManyToManyField("self", symmetrical=False, through="RelatedProduct", related_name="related_products")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_products", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_products", verbose_name="Modificado por")

    def __str__(self):
        return f"{self.sku} - {self.name}"

    #TODO: Product get_absolute_url
    #TODO: Prohibit a product being related to itself


class RelatedProduct(models.Model):
    class Meta:
        verbose_name = "Producto relacionado"
        verbose_name_plural = "Productos relacionados"
        constraints = [
            models.UniqueConstraint(fields=["product", "related_product"], name="product-related-unique")
        ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="related_links")
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reverse_links", verbose_name="Producto relacionado")

    def __str__(self):
        return f"{self.product.sku} > {self.related_product.sku}"