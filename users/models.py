from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings

class CustomUser(AbstractUser):
    def __str__(self):
        return self.get_full_name() or self.username


class Profile(models.Model):
    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"
        indexes = [
            models.Index(fields=["role"]),
        ]

    class Role(models.TextChoices):
        SALES = "S", "Vendedor"
        CSR = "C", "Servicio a clientes"
        MANAGER = "M", "Gerente"
        ADMIN = "A", "Administrador"

    phone_validator = RegexValidator(
        regex=r"^\d{10}$",
        message="El número de teléfono debe tener exactamente 10 dígitos numéricos."
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile", verbose_name="Usuario")
    role = models.CharField(max_length=1, choices=Role.choices, default=Role.SALES, verbose_name="Rol")
    phone = models.CharField(max_length=10, validators=[phone_validator], verbose_name="Teléfono oficina")
    cel_phone = models.CharField(max_length=10, validators=[phone_validator], verbose_name="Teléfono celular")
    position = models.CharField(max_length=30, verbose_name="Puesto")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    def formatted_phone(self):
        return f"({self.phone[:2]}){self.phone[2:6]}-{self.phone[6:]}"
    
    def formatted_cel_phone(self):
        return f"({self.cel_phone[:2]}){self.cel_phone[2:6]}-{self.cel_phone[6:]}"
    
    @property
    def is_sales(self):
        return self.role == self.Role.SALES

    @property
    def is_csr(self):
        return self.role == self.Role.CSR

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
