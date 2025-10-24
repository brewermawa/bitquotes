from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class Customer(models.Model):
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        indexes = [
            models.Index(fields=["assigned_to"]),
        ]

    rfc_validator = RegexValidator(
        regex=r"^([A-Za-zÑñ\x26]{3,4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))([A-Za-z\d]{3})?$",
        message="El RFC no tiene un formato válido"
    )


    name = models.CharField("Cliente", max_length=100, unique=True)
    rfc = models.CharField(max_length=13, validators=[rfc_validator])
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

