from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import HttpResponseRedirect

from .models import Customer
from users.models import CustomUser


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
    

    
                
