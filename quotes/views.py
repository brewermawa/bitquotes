from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.template.loader import get_template
from django.utils import timezone

from weasyprint import HTML

from .models import Quote, QuoteLine, QuoteSection, QuoteComment
from .forms import QuoteHeadForm, QuotePaymentTermsForm, QuoteLineForm, QuoteCommentForm
from users.models import CustomUser
from customers.models import Contact
from catalog.models import Product
from customers.models import Customer


@login_required
def dashboard(request):
    open = Quote.objects.open()
    won = Quote.objects.won()

    if request.user.profile.role != "M":
        open = open.filter(user=request.user)
        won = won.filter(user=request.user)

    now = timezone.now()
    won = won.filter(won_at__year=now.year, won_at__month=now.month)

    won_total = sum(q.total for q in won)

    ctx = {
        "open_quotes": open,
        "open_count": open.count(),
        "pending_approval": open.filter(status=Quote.Status.PENDING_APPROVAL).count(),
        "sent": open.filter(status=Quote.Status.SENT).count(),
        "won_total": won_total,
        "won_count": won.count()
    }

    return render(request, "quotes/dashboard.html", ctx)


class QuoteListView(LoginRequiredMixin, ListView):
    model = Quote
    template_name = "quotes/quotes_list.html"
    context_object_name = "quotes"
    ordering = "-created"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        slug = self.kwargs.get("slug")
        if slug:
            queryset = queryset.filter(customer__slug=slug)

        user = self.request.user
        if not (user.profile.is_csr or user.profile.is_manager):
            queryset = queryset.filter(user=user)

        selected_user_id = self.request.GET.get("user")
        if selected_user_id and (user.profile.is_csr or user.profile.is_manager):
            queryset = queryset.filter(user__id=selected_user_id)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["users"] = CustomUser.objects.all()
        context["can_see_all_quotes"] = self.request.user.profile.is_csr or self.request.user.profile.is_manager
        context["selected_user_id"] = self.request.GET.get("user") or ""
        context["slug"] = self.kwargs.get("slug")
        
        return context
    
    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get(self.page_kwarg, 1)
        page_obj = paginator.get_page(page)
        
        return paginator, page_obj, page_obj.object_list, page_obj.has_other_pages()

class QuoteHeadCreateView(LoginRequiredMixin, CreateView):
    model = Quote
    form_class = QuoteHeadForm
    template_name = "quotes/quote_head.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if not self.request.user.profile.is_csr and not self.request.user.profile.is_manager:
            form.instance.user = self.request.user

        response = super().form_valid(form)

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
    quote = get_object_or_404(Quote, pk=pk)
    discount_choices = QuoteLine.Discount.choices
    quote_line_form = QuoteLineForm()
    user = request.user

    # Reglas de edición por status (ajusta si cambias el workflow)
    if quote.status not in [
        quote.Status.DRAFT,
        quote.Status.APPROVED,
        quote.Status.PENDING_APPROVAL,
    ]:
        messages.warning(request, "No se puede editar una cotización en este status.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    # Permisos: solo CSR / manager pueden editar cualquier cotización.
    # Vendedor solo puede editar las suyas.
    if not (user.profile.is_csr or user.profile.is_manager):
        if quote.user != user:
            messages.error(
                request,
                f"No tienes permisos para editar la cotización {pk}.",
            )
            return redirect("quotes:quote_list")

    if request.method == "POST":
        # 1) Detectar líneas enviadas en el POST
        posted_lines = [
            key.split("_")[2]
            for key in request.POST.keys()
            if key.startswith("product_line_")
        ]

        # 2) Borrar líneas y secciones existentes para reconstruirlas
        QuoteLine.objects.filter(quote=quote).delete()
        QuoteSection.objects.filter(quote=quote).delete()

        # 3) Construir un diccionario de productos para evitar múltiples queries
        product_ids = []
        for line in posted_lines:
            product_id = request.POST.get(f"product_line_{line}")
            if product_id:
                product_ids.append(int(product_id))

        products_dict = Product.objects.in_bulk(product_ids)

        # 4) Recrear las líneas de cotización
        for line in posted_lines:
            product_id = int(request.POST.get(f"product_line_{line}"))
            quantity = int(request.POST.get(f"qty_line_{line}"))
            discount = int(request.POST.get(f"discount_line_{line}"))
            delivery_time = int(request.POST.get(f"delivery_line_{line}", 0) or 0)

            product = products_dict[product_id]

            # ---- NUEVO: unit_price editable (server-side) ----
            raw_unit_price = (request.POST.get(f"unit_price_line_{line}") or "").strip()
            try:
                unit_price = Decimal(raw_unit_price) if raw_unit_price else None
            except InvalidOperation:
                unit_price = None

            # Fallback seguro
            if unit_price is None:
                unit_price = product.price

            # Enforce server-side: solo editable si el producto lo permite
            if not product.price_editable:
                unit_price = product.price
            else:
                if unit_price < 0:
                    unit_price = Decimal("0.00")

            # IMPORTANTE: tu Quote.add_product debe aceptar unit_price
            quote.add_product(
                product=product,
                quantity=quantity,
                discount=discount,
                delivery_time=delivery_time,
                unit_price=unit_price,
            )

        # 5) Guardar términos de pago / condiciones de la cotización
        payment_terms_form = QuotePaymentTermsForm(request.POST, instance=quote)
        if payment_terms_form.is_valid():
            payment_terms_form.save()
        else:
            # Si quieres, aquí puedes mostrar errores, pero no bloqueamos el guardado de líneas
            pass

        # 6) Invalidate / reevaluate approval si estaba APPROVED o PENDING_APPROVAL
        quote.reevaluate_after_edit()

        messages.success(request, "La cotización se guardó correctamente.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    # GET: cargar formulario con la info actual
    payment_terms_form = QuotePaymentTermsForm(instance=quote)
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
    quote_qs = (
        Quote.objects
        .select_related("customer", "contact", "user")
        .prefetch_related(
            "quote_sections__section_lines__product",
            "quote_sections__section_lines",
        )
    )
    quote = get_object_or_404(quote_qs, pk=pk)
    comments = (
        QuoteComment.objects
        .filter(quote=quote)
        .select_related("user")
        .order_by("-created")
    )
    comment_form = QuoteCommentForm()

    return render(request, "quotes/quote_detail.html", {
        "quote": quote,
        "comments": comments,
        "comment_form": comment_form,
    })

@login_required
def quote_close_internal(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    user = request.user

    # 1) Permisos: CSR / manager pueden finalizar cualquier cotización.
    #    Vendedor solo puede finalizar sus propias cotizaciones.
    if not (user.profile.is_csr or user.profile.is_manager):
        if quote.user != user:
            messages.error(
                request,
                f"No tienes permisos para finalizar la cotización {pk}."
            )
            return redirect("quotes:quote_detail", pk=quote.pk)

    # 2) Solo se pueden finalizar cotizaciones en borrador
    if quote.status != Quote.Status.DRAFT:
        messages.warning(
            request,
            "Solo es posible finalizar cotizaciones en borrador."
        )
        return redirect("quotes:quote_detail", pk=quote.pk)

    # 3) Ejecutar lógica de cierre interno (APPROVED o PENDING_APPROVAL)
    quote.close_internal()

    # 4) Mensaje según el resultado
    if quote.status == Quote.Status.APPROVED:
        messages.success(
            request,
            "La cotización se finalizó y fue aprobada automáticamente."
        )
    elif quote.status == Quote.Status.PENDING_APPROVAL:
        messages.success(
            request,
            "La cotización se finalizó y ha sido enviada a aprobación interna."
        )
    else:
        # Esto no debería suceder con la lógica actual, pero dejamos un fallback defensivo
        messages.info(
            request,
            "La cotización se finalizó."
        )

    return redirect("quotes:quote_detail", pk=quote.pk)

    

@login_required
def quote_approve(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    user = request.user

    # Permisos: solo manager (y opcionalmente CSR)
    if not (user.profile.is_manager):
        messages.error(request, "No tienes permisos para aprobar esta cotización.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    # Solo tiene sentido aprobar si está en PENDING_APPROVAL
    if quote.status != Quote.Status.PENDING_APPROVAL:
        messages.warning(request, "Solo puedes aprobar cotizaciones en revisión.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    quote.approve(user=user)

    messages.success(request, "La cotización ha sido aprobada.")
    return redirect("quotes:quote_detail", pk=pk)

@login_required
def quote_send(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    user = request.user

    # Permisos
    if not (user.profile.is_csr or user.profile.is_manager or quote.user == user):
        messages.error(request, "No tienes permisos para enviar esta cotización.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    # Llamamos la lógica del modelo
    if quote.mark_sent(user=user):
        messages.success(request, "La cotización se ha marcado como enviada.")
    else:
        messages.warning(request, "Solo puedes enviar cotizaciones aprobadas.")

    return redirect("quotes:quote_detail", pk=quote.pk)

@login_required
def quote_mark_won(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    user = request.user

    if not (user.profile.is_csr or user.profile.is_manager or quote.user == user):
        messages.error(request, "No tienes permisos para actualizar esta cotización.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    if quote.mark_won(user=user):
        messages.success(request, "La cotización se ha marcado como ganada.")
    else:
        messages.warning(request, "Solo puedes marcar como ganada una cotización enviada.")

    return redirect("quotes:quote_detail", pk=quote.pk)


@login_required
def quote_mark_lost(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    user = request.user

    if not (user.profile.is_csr or user.profile.is_manager or quote.user == user):
        messages.error(request, "No tienes permisos para actualizar esta cotización.")
        return redirect("quotes:quote_detail", pk=quote.pk)

    if quote.mark_lost(user=user):
        messages.success(request, "La cotización se ha marcado como perdida.")
    else:
        messages.warning(request, "Solo puedes marcar como perdida una cotización enviada.")

    return redirect("quotes:quote_detail", pk=quote.pk)

@login_required
def quote_add_comment(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    if request.method == "POST":
        form = QuoteCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.quote = quote
            comment.user = request.user
            comment.save()

            # Recargamos comentarios y limpiamos el form
            comments = quote.comments.select_related("user").order_by("-created")
            form = QuoteCommentForm()

            return render(
                request,
                "quotes/_quote_comments_block.html",
                {
                    "quote": quote,
                    "comment_form": form,
                    "comments": comments,
                },
            )

    # Si algo falla en el form, regresamos el bloque igual pero con errores
    comments = quote.comments.select_related("user").order_by("-created")
    form = QuoteCommentForm(request.POST or None)

    return render(
        request,
        "quotes/partials/_quote_comments_block.html",
        {
            "quote": quote,
            "comment_form": form,
            "comments": comments,
        },
        status=400,
    )
    

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

def quote_pdf_test(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    template = get_template("quotes/quote_pdf.html")
    html_string = template.render({
        "quote": quote,
        "request": request,
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_bytes = html.write_pdf()

    filename = f"TEST-cotizacion-{quote.id}.pdf"

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
