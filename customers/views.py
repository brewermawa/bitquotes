from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Customer
from users.models import CustomUser


class ClientListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    ordering = ["name"]
    paginate_by = 10

    def get_queryset(self):
        #TODO: Búsqueda por RFC
        queryset = super().get_queryset().select_related("assigned_to")
        q = self.request.GET.get("q")
        assigned = self.request.GET.get("assigned")


        if (not q and not assigned) or not assigned.isdigit():
            return queryset
        
        if q and not assigned:
            return queryset.filter(name__icontains=q.strip())
        
        if not q and (assigned):
            return queryset.filter(assigned_to_id=assigned)
        
        return queryset.filter(name__icontains=q.strip()).filter(assigned_to_id=assigned)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = CustomUser.objects.filter(is_active=True)
        return context
    
    
                
