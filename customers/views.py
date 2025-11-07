from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Customer


class ClientListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    ordering = ["name"]
    paginate_by = 10