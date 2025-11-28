import re
import json
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .models import Customer, Contact
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
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        return super().form_valid(form)
    
    
class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contacts"] = self.object.contacts.all()

        return context
    
    def get_queryset(self):
        return Customer.objects.select_related("assigned_to").prefetch_related("contacts")
        
    
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
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")

    customer = get_object_or_404(Customer, pk=pk)

    name = _clean_str(request.POST.get("name"))
    rfc = _clean_str(request.POST.get("rfc")).upper()
    assigned_to = request.POST.get("assigned_to")

    errors = {}
    if not name:
        errors["name"] = "El nombre/razón social es obligatorio."

    if rfc:
        if not RFC_REGEX.match(rfc):
            errors["rfc"] = "Formato de RFC inválido."
        else:
            if Customer.objects.exclude(pk=customer.pk).filter(rfc__iexact=rfc).exists():
                errors["rfc"] = "El RFC ya existe en el sistema."
    else:
        errors["rfc"] = "El RFC es obligatorio."

    if errors:
        customer.name = name
        customer.rfc = rfc
        customer.assigned_to_id = assigned_to or None
        
        context = {
            "customer": customer,
            "errors": errors,
            "users": CustomUser.objects.filter(is_active=True),
        }
        response = render(request, "customers/_customer_row_edit.html", context)

        return response

    # Persistir cambios
    customer.name = name
    customer.rfc = rfc
    print("---" + assigned_to)
    customer.assigned_to = CustomUser.objects.get(pk=assigned_to)

    # Opcional: si llevas auditoría
    if hasattr(customer, "updated_by"):
        customer.updated_by_id = request.user.id

    customer.save(update_fields=["name", "rfc", "assigned_to", "updated_by"])

    customer.refresh_from_db()
    context = {"customer": customer}
    response = render(request, "customers/_customer_row_readonly.html", context)

    response["HX-Trigger"] = json.dumps({
        "toast": {
            "message": f"Cliente {customer} actualizado correctamente",
            "level": "success"  # success | info | warning | danger
        }
    })
    
    return response

class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    fields = [
        "first_name", "last_name", "title", "phone", "phone_extension",
        "cel_phone", "email", "is_active"
    ]
    template_name = "customers/contact_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = self.customer

        return context
    
    def form_valid(self, form):
        form.instance.customer = self.customer
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        return super().form_valid(form)
    
    def get_success_url(self):
        return self.customer.get_absolute_url()
    

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    fields = [
        "first_name", "last_name", "title", "phone", "phone_extension",
        "cel_phone", "email", "is_active"
    ]
    template_name = "customers/contact_edit.html"
    context_object_name = "contact"

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = self.customer

        return context
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        return super().form_valid(form)
    
    def get_success_url(self):
        return self.customer.get_absolute_url()
    
@login_required
def contact_toggle(request, slug, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    contact = get_object_or_404(Contact, pk=pk, customer__slug=slug)
    contact.is_active = not contact.is_active
    contact.save()

    customer = get_object_or_404(Customer, pk=contact.customer.pk)

    response = render(request, "customers/contact_toggle.html", {
        "customer": customer,
        "c": contact,
    })

    response["HX-Trigger"] = json.dumps({
        "toast": {
            "message": f"Contacto {'activado' if contact.is_active else 'desactivado'} correctamente",
            "level": "success"
        }
    })
    return response

@login_required
def customer_search_htmx(request):
    term = request.GET.get("search", "")
    customers = Customer.objects.filter(name__icontains=term)[:10]

    return render(request, "customers/_customer_search_list.html", {
        "customers": customers
    })

@login_required
def contacts_for_quote_htmx(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    contacts = customer.contacts.filter(is_active=True).order_by("first_name", "last_name")

    return render(request, "customers/_contacts_for_quote_select.html", {
        "customer": customer,
        "contacts": contacts,
    })
