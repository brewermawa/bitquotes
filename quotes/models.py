from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
from calendar import monthrange
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from customers.models import Customer, Contact


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

    quote_id = models.CharField(max_length=19, unique=True, verbose_name="Cotización", blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Cliente", related_name="customer_quotes")
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name="contact_quotes", verbose_name="Contacto")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="user_quotes", verbose_name="Usuario",)
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

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["status", "created"])
        ]
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        get_latest_by = "created"

    def __str__(self):
        return self.quote_id

    def clean(self):
        if self.contact.customer != self.customer:
            raise ValidationError(message="El contacto seleccionado no es parte del cliente seleccionado")

        return super().clean()
    
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