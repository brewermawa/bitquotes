from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def document_upload_path(instance, filename):
        sku = instance.product.sku.replace(" ", "_")
        return f"documents/{sku}/{filename}"

class Category(models.Model):
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        indexes = [models.Index(fields=["name"]),]

    name = models.CharField(max_length=30, unique=True, verbose_name="Categoría")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="created_categories", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="updated_categories", verbose_name="Modificado por")

    def save(self, *args, **kwargs):
        if self.pk: #only runs when editing a category, not when saving a new one
            #gets the category from the database (only the is_active field)
            old_is_active = Category.objects.filter(pk=self.pk).only("is_active").first()

            if old_is_active and not self.is_active:
                self.products.update(is_active=False)

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
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

    sku = models.CharField(max_length=10, unique=True, verbose_name="Número de parte")
    name = models.CharField(max_length=100, verbose_name="Producto")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name="Descripción")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio")
    product_type = models.CharField(max_length=3, choices=ProductType.choices, default=ProductType.CONSUMIBLE, verbose_name="Tipo de producto")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    related_product = models.ManyToManyField("self", symmetrical=False, through="RelatedProduct", related_name="related_products")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="created_products", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="updated_products", verbose_name="Modificado por")

    def clean(self):
        self.sku = self.sku.strip().upper()
        self.name = self.name.strip()

        if self.description:
            self.description = self.description.strip()

        if self.price is not None and self.price <= 0:
            raise ValidationError({"price": "El precio debe ser mayor a 0."})

    def __str__(self):
        return f"{self.sku} - {self.name}"

    #TODO: Product get_absolute_url


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
    

class ProductDocument(models.Model):
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["product", "document_type", "name"]
        constraints = [
            models.UniqueConstraint(fields=["product", "document_type"], name="product_document_unique")
        ]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    class DocumentType(models.TextChoices):
        FICHA_TECNICA = "FTE", "Ficha técnica"
        MANUAL = "MAN", "Manual"
        GARANTIA = "GAR", "Garantía"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="documents", verbose_name="Producto")
    name = models.CharField(max_length=100, verbose_name="Documento")
    document_type = models.CharField("Tipo de documento", max_length=3, choices=DocumentType.choices, default=DocumentType.FICHA_TECNICA)
    document = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        verbose_name="Archivo PDF"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="created_product_documents", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="updated_product_documents", verbose_name="Modificado por")

    def clean(self):
        self.name = self.name.strip()

    def __str__(self):
        return f"{self.product.sku} - {self.name}"
