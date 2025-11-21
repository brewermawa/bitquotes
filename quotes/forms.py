from django import forms

from .models import Quote, QuoteLine
from customers.models import Contact
from users.models import CustomUser


class QuoteHeadForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["customer", "contact", "user"]
        error_messages = {
            "customer": {"required": "Es necesario seleccionar un cliente", },
            "contact": {"required": "Es necesario seleccionar un contacto", },
            "user": {"required": "Es necesario seleccionar un usuario", },
        }

    def __init__(self,*args, **kwargs):
        print("FORM init")
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        customer_id = None
        data = self.data or None
        if data and data.get(self.add_prefix("customer")):
            customer_id = data.get(self.add_prefix("customer"))
        elif self.instance and self.instance.pk and self.instance.customer_id:
            customer_id = self.instance.customer_id

        if customer_id:
            self.fields["contact"].queryset = Contact.objects.filter(customer_id=customer_id, is_active=True).order_by("first_name", "last_name")
        else:
            self.fields["contact"].queryset = Contact.objects.none()

        if hasattr(self.request_user, "profile") and (self.request_user.profile.is_csr or self.request_user.profile.is_manager):
            # CSR/Manager: pueden asignar a un SalesRep activo
            self.fields["user"].queryset = CustomUser.objects.filter(is_active=True).order_by("first_name", "last_name", "username")
        else:
            # Sales u otros: no elige, se asigna a sí mismo (campo oculto)
            if "user" in self.fields:
                self.fields["user"].widget = forms.HiddenInput()
                self.fields["user"].initial = self.request_user

    def clean(self):
        """
        Validación amistosa: el contacto debe pertenecer al cliente elegido.
        (Tu modelo ya lo valida en clean(), pero esto mejora el mensaje en el form.)
        """
        print("FORM clean")
        cleaned = super().clean()
        customer = cleaned.get("customer")
        contact = cleaned.get("contact")

        if customer and contact and contact.customer_id != customer.id:
            self.add_error("contact", "El contacto no pertenece al cliente seleccionado.")
            
        return cleaned

class QuotePaymentTermsForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["payment_terms"]
        widgets = {
            "payment_terms": forms.Select(
                attrs={
                    "class": "form-select form-select-sm",
                }
            )
        }

class QuoteLineForm(forms.ModelForm):
    class Meta:
        model = QuoteLine
        fields = [
            "product",
            "description",
            "quantity",
            "unit_price",
            "discount",
            "delivery_time"
        ]    
    
