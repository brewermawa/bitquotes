from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseBadRequest, HttpResponse
from django.db.models import Q

from .models import Quote, QuoteLine
from .forms import QuoteHeadForm, QuotePaymentTermsForm, QuoteLineForm
from users.models import CustomUser
from customers.models import Contact
from catalog.models import Product

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
        response = super().form_valid(form)
        print("---", self.object.pk)

        return response
    
    def get_success_url(self):
        return reverse("quotes:quote_edit", kwargs={"pk": self.object.pk})
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")

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
    if request.method == "GET":
        print("cargando en GET")

    if request.method == "POST":
        print("cargando en POST")
        for k, v in request.POST.items():
            print(k, "=>", v)

    quote = get_object_or_404(Quote, pk=pk)
    quote_line_form = QuoteLineForm()
    payment_terms_form = QuotePaymentTermsForm(instance=quote)
    discount_choices = QuoteLine.Discount.choices

    quote_lines = QuoteLine.objects.filter(quote=quote)

    return render(request, "quotes/quote_edit.html", {
        "quote_line_form": quote_line_form,
        "payment_terms_form": payment_terms_form,
        "quote": quote,
        "quote_lines": quote_lines,
        "discount_choices": discount_choices,
    })

@login_required
def quote_detail(request, pk):

    quote = get_object_or_404(Quote, pk=pk)

    return render(request, "quotes/quote_detail.html", {
        "quote": quote
    })
    

def load_users_htmx(request):
    users = CustomUser.objects.filter(is_active=True)
    
    return render(request, "quotes/_users_select_options.html", {"users": users})

@login_required
def product_search_htmx(request):
    search_term = (request.GET.get("product_search") or "").strip()

    if not search_term:
        return render(request, "quotes/_product_search.html", {
            "products": []
        })

    query = Q(name__icontains=search_term) | Q(sku__icontains=search_term)
    products = Product.objects.filter(query).order_by("name")[:10]
    
    return render(request, "quotes/_product_search.html", {
        "products": products
    })

@login_required
def related_products(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = product.related_product.all()
    
    return render(request, "quotes/_related_products.html", {
        "product": product,
        "related_products": related_products,
    })

#TODO: Cuando se seleccione un producto en el buscador para agregar línea, reiniciar el buscador

