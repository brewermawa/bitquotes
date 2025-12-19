from django import forms

from .models import Quote, QuoteLine, QuoteComment
from customers.models import Contact
from users.models import CustomUser


class QuoteHeadForm(forms.ModelForm):

    class Meta:
        model = Quote
        fields = ["customer", "contact", "user"]
        error_messages = {
            "customer": {"required": "Es necesario seleccionar un cliente"},
            "contact": {"required": "Es necesario seleccionar un contacto"},
            "user": {"required": "Es necesario seleccionar un usuario"},
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # ----------------------------
        # Contactos dependientes del cliente
        # ----------------------------
        customer_id = None
        data = self.data or None

        if data and data.get(self.add_prefix("customer")):
            customer_id = data.get(self.add_prefix("customer"))
        elif self.instance and self.instance.pk and self.instance.customer_id:
            customer_id = self.instance.customer_id

        if customer_id:
            self.fields["contact"].queryset = (
                Contact.objects
                .filter(customer_id=customer_id, is_active=True)
                .order_by("first_name", "last_name")
            )
        else:
            self.fields["contact"].queryset = Contact.objects.none()

        # ----------------------------
        # Asignación de usuario según rol
        # ----------------------------
        if (
            self.request_user
            and hasattr(self.request_user, "profile")
            and (self.request_user.profile.is_csr or self.request_user.profile.is_manager)
        ):
            # CSR / Manager: pueden elegir usuario
            self.fields["user"].queryset = (
                CustomUser.objects
                .filter(is_active=True)
                .order_by("first_name", "last_name", "username")
            )
        else:
            # Vendedor u otros: NO puede elegir usuario
            # Quitamos el campo del form para evitar validación y POST malicioso
            self.fields.pop("user", None)

            # Dejamos el instance consistente desde el inicio
            if self.request_user:
                self.instance.user = self.request_user

    def clean(self):
        """
        Validación amigable:
        el contacto debe pertenecer al cliente seleccionado.
        """
        cleaned = super().clean()
        customer = cleaned.get("customer")
        contact = cleaned.get("contact")

        if customer and contact and contact.customer_id != customer.id:
            self.add_error(
                "contact",
                "El contacto no pertenece al cliente seleccionado."
            )

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


class QuoteCommentForm(forms.ModelForm):
    class Meta:
        model = QuoteComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(attrs={
                "class": "form-control form-control-sm",
                "rows": "3",
                "placeholder": "Comentario",
            })
        }
    
