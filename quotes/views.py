from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Quote
from .forms import QuoteHeadForm
from users.models import CustomUser
from customers.models import Contact

@login_required
def dashboard(request):
    return render(request, "quotes/dashboard.html")


def quote_list(request):
    return render(request, "quotes/quotes_list.html", {})

class QuoteHeadCreateView(LoginRequiredMixin, CreateView):
    model = Quote
    form_class = QuoteHeadForm
    template_name = "quotes/quote_head.html"
    #success_url = reverse_lazy("quotes:quote_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if not self.request.user.profile.is_csr and not self.request.user.profile.is_manager:
            form.instance.user = self.request.user

        print("***********************")

        #response = super().form_valid(form)

        return redirect("quotes:quote_edit", pk=self.object.pk)
        
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")

        print("------------------------")

        customer_id = None
        if self.request.method == "POST":
            customer_id = self.request.POST.get("customer")
        else:
            customer_id = form.instance.customer_id

        if customer_id:
            context["contacts"] = Contact.objects.filter(
                customer_id=customer_id,
                is_active=True,
            ).order_by("first_name", "last_name")
        else:
            context["contacts"] = None

        return context
    
@login_required
def quote_edit(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    return render(request, "quotes/quote_detail.html", {
        "quote": quote
    })

@login_required
def quote_detail(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    return render(request, "quotes/quote_edit.html", {
        "quote": quote
    })
    

def load_users_htmx(request):
    users = CustomUser.objects.filter(is_active=True)
    
    return render(request, "quotes/_users_select_options.html", {"users": users})