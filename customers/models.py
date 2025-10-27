from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings


class Customer(models.Model):
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["assigned_to"]),
        ]

    rfc_validator = RegexValidator(
        regex=r"^([A-Za-zÑñ\x26]{3,4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))([A-Za-z\d]{3})?$",
        message="El RFC no tiene un formato válido"
    )

    name = models.CharField("Cliente", max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    rfc = models.CharField(max_length=13, validators=[rfc_validator])
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vendedor", related_name="assigned_customers")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_customers")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_customers")

    def formatted_rfc(self):
        if self.rfc[3].isdigit():
            return f"{self.rfc[:3]}-{self.rfc[3:9]}-{self.rfc[9:]}"
        
        return f"{self.rfc[:4]}-{self.rfc[4:10]}-{self.rfc[10:]}"
    
    def __str__(self):
        return self.name
    
    #TODO: Customer get_absolute_url
    

class Contact(models.Model):
    class Meta:
        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"
        ordering = ["first_name", "last_name"]
        indexes = [
            models.Index(fields=["first_name", "last_name"]),
            models.Index(fields=["customer"]),
        ]

    phone_validator = RegexValidator(
        regex=r"^\d{10}$",
        message="El número de teléfono debe tener exactamente 10 dígitos numéricos."
    )

    first_name = models.CharField("Nombre", max_length=20)
    last_name = models.CharField("Apellido", max_length=20)
    phone = models.CharField("Teléfono oficina", max_length=10, validators=[phone_validator])
    phone_extension = models.CharField("Extensión", max_length=6, null=True, blank=True)
    cel_phone = models.CharField("Teléfono celular", max_length=10, validators=[phone_validator])
    email = models.EmailField(unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    is_active = models.BooleanField("Activo", default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_contacts")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_contacts")

    def __str__(self):
        return f"{self.first_name} - {self.last_name}"
    
    #TODO: Contact get_absolute_url

    

    
