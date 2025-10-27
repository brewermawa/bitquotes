from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

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

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile", verbose_name="Usuario")
    role = models.CharField("rol", max_length=1, choices=Role.choices, default=Role.SALES)
    phone = models.CharField("Teléfono oficina", max_length=10, validators=[phone_validator])
    cel_phone = models.CharField("Teléfono celular", max_length=10, validators=[phone_validator])
    position = models.CharField("Puesto", max_length=30)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    def formatted_phone(self):
        return f"({self.phone[:2]}){self.phone[2:6]}-{self.phone[6:]}"
    
    def formatted_cel_phone(self):
        return f"({self.cel_phone[:2]}){self.cel_phone[2:6]}-{self.cel_phone[6:]}"
