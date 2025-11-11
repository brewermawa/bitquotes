import re
import json
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .models import Customer
from users.models import CustomUser

RFC_REGEX = re.compile(r"^([A-Za-zÑñ\x26]{3,4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))([A-Za-z\d]{3})?$")

def _clean_str(value: str) -> str:
    return (value or "").strip()

class CustomerListBase(LoginRequiredMixin, ListView):
    model = Customer
    context_object_name = "customers"
    ordering = ["name"]
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q", "")
        if q:
            queryset = queryset.filter(name__icontains=q) | queryset.filter(rfc__icontains=q)
                
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = CustomUser.objects.filter(is_active=True)

        return context
    
    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get(self.page_kwarg, 1)
        page_obj = paginator.get_page(page)
        
        return paginator, page_obj, page_obj.object_list, page_obj.has_other_pages()
    

class CustomerListView(CustomerListBase):
    template_name = "customers/customer_list.html"

class CustomerListPartialView(CustomerListBase):
    template_name = "customers/_customers_table.html"

    def get(self, request, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST") != "true":
            return HttpResponseRedirect(reverse("customers:customer_list"))
        
        response = super().get(request, *args, **kwargs)

        base_url = reverse("customers:customer_list")
        query = request.GET.urlencode()
        clean_url = f"{base_url}?{query}" if query else base_url

        response["HX-Push-Url"] = clean_url
        
        return response
    
class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    fields = ["name", "rfc", "assigned_to"]
    template_name = "customers/new_customer.html"
    success_url = reverse_lazy("customers:customer_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = CustomUser.objects.filter(is_active=True)
        
        return context
    
    
@login_required
def customer_row_edit(request, pk):
    """
    Devuelve SOLO el <tr> en modo edición para el customer dado.
    Si NO viene de HTMX y entran directo, redirige a la lista.
    """
    if request.META.get("HTTP_HX_REQUEST") != "true":
        return HttpResponseRedirect(reverse("customers:customer_list"))

    customer = get_object_or_404(Customer.objects.select_related("assigned_to"), pk=pk)
    return render(request, "customers/_customer_row_edit.html", {
        "customer": customer,
        "users": CustomUser.objects.filter(is_active=True),
        "errors": {},
    })
    
@login_required
def customer_row_readonly(request, pk):
    """
    Devuelve SOLO el <tr> en modo lectura para el customer dado.
    """
    customer = get_object_or_404(Customer.objects.select_related("assigned_to"), pk=pk)
    return render(request, "customers/_customer_row_readonly.html", {
        "customer": customer,
    })


@login_required
def customer_row_update(request, pk):
    """
    Procesa el POST de 'Guardar' de la fila editable.
    - Valida nombre y RFC (formato + unicidad).
    - Actualiza y devuelve el <tr> en modo lectura si OK.
    - Si hay errores, devuelve el <tr> en modo edición con mensajes (HTTP 422).
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")

    customer = get_object_or_404(Customer, pk=pk)

    name = _clean_str(request.POST.get("name"))
    rfc = _clean_str(request.POST.get("rfc")).upper()
    assigned_to = request.POST.get("assigned_to")

    errors = {}
    # Validaciones básicas
    if not name:
        errors["name"] = "El nombre/razón social es obligatorio."

    if rfc:
        if not RFC_REGEX.match(rfc):
            errors["rfc"] = "Formato de RFC inválido."
        else:
            # Unicidad de RFC (excluyendo al propio registro)
            if Customer.objects.exclude(pk=customer.pk).filter(rfc__iexact=rfc).exists():
                errors["rfc"] = "El RFC ya existe en el sistema."
    else:
        # Si tu modelo permite RFC vacío, elimina este bloque.
        errors["rfc"] = "El RFC es obligatorio."

    if errors:
        # Responder la MISMA fila en modo edición con errores (422 = Unprocessable Entity)
        ctx = {"customer": customer, "errors": errors}
        response = render(request, "customers/_customer_row_edit.html", ctx)
        return response

    # Persistir cambios
    customer.name = name
    customer.rfc = rfc
    customer.assigned_to = CustomUser.objects.get(id=assigned_to)

    # Opcional: si llevas auditoría
    if hasattr(customer, "updated_by_id"):
        customer.updated_by_id = request.user.id
    customer.save(update_fields=["name", "rfc", "assigned_to"] + (["updated_by"] if hasattr(customer, "updated_by") else []))

    # Devolver la fila en modo lectura
    customer.refresh_from_db()
    ctx = {"customer": customer}
    response = render(request, "customers/_customer_row_readonly.html", ctx)

    response["HX-Trigger"] = json.dumps({
        "toast": {
            "message": f"Cliente {customer} actualizado correctamente",
            "level": "success"  # success | info | warning | danger
        }
    })
    
    return response

                
