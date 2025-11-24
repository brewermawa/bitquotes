from django.urls import path

from . import views

app_name = "quotes"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("list/", views.quote_list, name="quote_list"),
    
    # PASO 1: encabezado de cotización
    path("new/", views.QuoteHeadCreateView.as_view(), name="quote_create"),

    # PASO 2: Agregar líneas a cotización o editar cotización
    path("<int:pk>/edit/", views.quote_edit, name="quote_edit"),

    # Ver detalles de cotización
    path("<int:pk>/", views.quote_detail, name="quote_detail"),
    
    path("load-users-htmx/", views.load_users_htmx, name="load_users_htmx"),
    path("product-search-htmx/", views.product_search_htmx, name="product_search_htmx"),

    #Productos relacionados.
    path("product/<int:pk>/related/", views.related_products, name="related_products"),
] 
