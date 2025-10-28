from django.db import models
from django.conf import settings

from customers.models import Customer, Contact
from users.models import CustomUser


class Quote(models.Model):
    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"

    class Status(models.TextChoices):
        DRAFT = "DFT", "Vendedor"
        PENDING_APPROVAL = "RVW", "Aprobación pendiente"
        APPROVED = "APP", "" "Aprobada"
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

    quote_id = models.CharField("Cotización", max_length=19, unique=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Cliente", related_name="customer_uotes")
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT, verbose_name="Contacto", related_name="contact_quotes")
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name="Usuario", related_name="user_quotes")
    status = models.CharField("Estatus", max_length=3, choices=Status.choices, default=Status.DRAFT)
    payment_terms = models.CharField("términos de pago", max_length=3, choices=PaymentTerms.choices, default=PaymentTerms.CASH)
    
    # El campo valid_until debe ser el último día del mes cuando se hace la cotización. Si el último día del mes está
    # a menos de 5 días de la fecha de la cotización, valid_until será el día 15 del siguiente mes
    valid_until = models.DateField(verbose_name="Válida hasta")
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Subtotal")
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Descuento")
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_quotes", verbose_name="Creado por")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_quotes", verbose_name="Modificado por")

    def clean(self):
        return super().clean()

    def __str__(self):
        return super().__str__()

    
