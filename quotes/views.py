from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Quote
from .forms import QuoteForm
from users.models import CustomUser
from customers.models import Contact

@login_required
def dashboard(request):
    return render(request, "quotes/dashboard.html")


def quote_list(request):
    return render(request, "quotes/quotes_list.html", {})

class QuoteCreateView(LoginRequiredMixin, CreateView):
    model = Quote
    form_class = QuoteForm
    template_name = "quotes/quote_form.html"
    success_url = reverse_lazy("quotes:quote_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if not self.request.user.profile.is_csr and not self.request.user.profile.is_manager:
            form.instance.user = self.request.user

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")

        if form is not None and form.instance.customer_id:
            context["contacts"] = Contact.objects.filter(
                customer_id=form.instance.customer_id,
                is_active=True,
            ).order_by("first_name", "last_name")
        else:
            context["contacts"] = None

        return context
    

def load_users_htmx(request):
    users = CustomUser.objects.filter(is_active=True)
    
    return render(request, "quotes/_users_select_options.html", {"users": users})