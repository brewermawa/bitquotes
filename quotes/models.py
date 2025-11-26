from django.db import models
from django.conf import settings
from datetime import date
from calendar import monthrange
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP

from customers.models import Customer, Contact
from catalog.models import Product


class Quote(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DFT", "Borrador"
        PENDING_APPROVAL = "RVW", "Aprobación pendiente"
        APPROVED = "APP", "Aprobada"
        SENT = "SNT", "Enviada"
        WON = "WON", "Ganada"
        LOST = "LST", "Perdida"
        EXPIRED = "EXP", "Expirada"
        #Como se va a marcar una cotización como expirada?

    class PaymentTerms(models.TextChoices):
        CASH = "CSH", "Contado"
        N7 = "N07", "Crédito 7 días"
        N15 = "N15", "Crédito 15 días"
        N30 = "N30", "Crédito 30 días"
        N60 = "N60", "Crédito 60 días"
        N90 = "N90", "Crédito 90 días"

    # El identificador de la cotización va a ener el formato BIT-NA-YYMMDD-#####, donde:
    # - 'BIT' siempre es constante
    # - 'NA' son las iniciales del nombre y el apellido del creador de la cotización
    # - 'YY' son los dos últimos dígitos del año; ej: 2025: 25
    # - 'MM' es el mes. Siempre a 2 dígitos.
    # - 'DD' es el día. Siempre a 2 dígitos.
    # - '#####' es un consecutivo, siempre de 5 dígitos, justificado con ceros a la
    # izquierda. Va a tomar el número del pk del modelo. ej si pk = 16, el consecutivo
    # será '00016' para unb identificador completo: BIT-MG-251028-00016

    quote_id = models.CharField(max_length=19, unique=True, blank=True, null=True, verbose_name="Cotización")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Cliente", related_name="customer_quotes")
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name="contact_quotes", verbose_name="Contacto")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="user_quotes", verbose_name="Usuario")
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.DRAFT, verbose_name="Estatus")
    payment_terms = models.CharField(max_length=3, choices=PaymentTerms.choices, default=PaymentTerms.CASH, verbose_name="Términos de pago")
    
    # El campo valid_until debe ser el último día del mes cuando se hace la cotización. Si el último día del mes está
    # a menos de 5 días de la fecha de la cotización, valid_until será el día 15 del siguiente mes
    valid_until = models.DateField(verbose_name="Válida hasta", blank=True, null=True)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Subtotal")
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Descuento")
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Total")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="created_quotes", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="updated_quotes", verbose_name="Modificado por")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="approved_quotes", verbose_name="Aprobada por")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de aprobación")
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="sent_quotes", verbose_name="Enviada por")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de envío")
    won_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="won_quotes", verbose_name="Ganada por")
    won_at = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de cierre")
    lost_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="lost_quotes", verbose_name="Perdida por")
    lost_at = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de pérdida")
    lost_reason = models.CharField(max_length=100, blank=True, null=True, verbose_name="Razón de pérdida")

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["status", "created"]),
            models.Index(fields=["user", "created"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        get_latest_by = "created"

    def __str__(self):
        return self.quote_id

    def clean(self):
        #Validar que el contacto sea parte del cliente seleccionado.
        if self.customer_id and self.contact_id:
            if self.contact.customer_id != self.customer_id:
                raise ValidationError({"contact": "El contacto no es parte del cliente seleccionado"})

        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()

        return super().save(*args, **kwargs)
    
    def __set_valid_until(self):
        #today = timezone.localdate()
        today = self.created
        last_day_of_month = today.replace(day=monthrange(today.year, today.month)[1])
        if (last_day_of_month - today).days < 5:
            year = today.year + 1 if today.month == 12 else today.year
            month = 1 if today.month == 12 else today.month + 1
            self.valid_until = date(year, month, 15)
        else:
            self.valid_until = last_day_of_month

    def __set_quote_id(self):
        #BIT-MG-251028-00016
        initials = f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        #date_part = timezone.localdate().strftime("%y%m%d")
        date_part = self.created.strftime("%y%m%d")
        pk_part = str(self.pk).zfill(5)
        self.quote_id = f"BIT-{initials}-{date_part}-{pk_part}"
    
    def save(self, *args, **kwargs):
        #grabo el modelo con información parcial para obtener el pk
        super().save(*args, **kwargs)

        #fecha de validez al último día de mes o al 15 del días siguiente si faltan menos de 5 días
        if not self.valid_until:
            self.__set_valid_until()

        if not self.quote_id:
            self.__set_quote_id()
       
        return super().save(*args, **kwargs)
    
    def assign_section(self, product):
        section_type = product.product_type
        section_name = product.get_product_type_display()

        section = QuoteSection.objects.filter(quote=self, section_type=section_type).first()

        if not section: #No existe la sección
            section = QuoteSection.objects.create(quote=self, section_type=section_type, name=section_name)

        return section
            
    

class QuoteSection(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="quote_sections")
    name = models.CharField(max_length=50, verbose_name="Sección")
    section_type = models.CharField(max_length=3, verbose_name="Tipo de sección", default="")
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Subtotal")

    class Meta:
        verbose_name = "Sección de cotización"
        verbose_name_plural = "Secciones de cotización"
        indexes = [
            models.Index(fields=["name"])
        ]
        constraints = [models.UniqueConstraint(fields=["name", "quote"], name="unique_section_per_quote")]

    def __str__(self):
        return f"{self.quote} - {self.name}"
    

class QuoteLine(models.Model):
    class Discount(models.IntegerChoices):
        DISC0 = 0, "0%"
        DISC3 = 3, "3%"
        DISC5 = 5, "5%"
        DISC7 = 7, "7%"
        DISC10 = 10, "10%"
        DISC15 = 15, "15%"
        DISC50 = 50, "50%"
        DISC100 = 100, "100%"

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="quote_lines")
    section = models.ForeignKey(QuoteSection, on_delete=models.SET_NULL, blank=True, null=True, related_name="section_lines", verbose_name="Sección")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="product_quoted_lines", verbose_name="Número de parte")
    description = models.CharField(max_length=200, blank=True, verbose_name="Descripción")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad")
    unit_price = models.DecimalField(max_digits=12, validators=[MinValueValidator(0)], decimal_places=2, verbose_name="Precio unitario")
    discount = models.PositiveSmallIntegerField(choices=Discount.choices, default=Discount.DISC0, blank=False, null=False, verbose_name="Descuento")
    delivery_time = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Tiempo de entrega", help_text="Tiempo en días hábiles")

    class Meta:
        verbose_name = "Línea de cotización"
        verbose_name_plural = "Líneas de cotización"
        ordering = ["section_id", "id"]
        indexes = [
            models.Index(fields=["quote"]),
            models.Index(fields=["section"]),
            models.Index(fields=["product"]),
            models.Index(fields=["discount"]),
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity} ({self.discount}%)"

    # Snapshot básico
    def save(self, *args, **kwargs):
        if not self.description:
            self.description = getattr(self.product, "name", str(self.product))[:200]
        super().save(*args, **kwargs)


    @property
    def gross_total(self) -> Decimal:
        return (Decimal(self.quantity) * (self.unit_price or Decimal("0.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def discount_value(self) -> Decimal:
        pct = Decimal(self.discount or 0) / Decimal("100")
        return (self.gross_total * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def net_total(self) -> Decimal:
        return (self.gross_total - self.discount_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class QuoteComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quote_comments", verbose_name="Usuario")
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField(verbose_name="Comentario")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["quote"]),
            models.Index(fields=["quote", "created"])
        ]

    def __str__(self):
        return f"Comentario de {self.user} en {self.quote}"
