from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Quote
from .forms import QuoteForm
from users.models import CustomUser

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

        if not self.request.user.profile.is_csr and not self.request_user.profile.is_manager:
            form.instance.user = self.request.user

        return super().form_valid(form)