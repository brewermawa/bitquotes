from django.urls import path

from . import views

app_name = "quotes"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("list/", views.QuoteListView.as_view(), name="quote_list"),
    path("list/<slug:slug>", views.QuoteListView.as_view(), name="quote_list_customer"),
    
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

    path("<int:pk>/comments/add/", views.quote_add_comment, name="quote_add_comment"),
    path("<int:pk>/approve/", views.quote_approve, name="quote_approve"),
    path("<int:pk>/close_internal/", views.quote_close_internal, name="quote_close_internal"),
    path("<int:pk>/mark_won/", views.quote_mark_won, name="quote_mark_won"),
    path("<int:pk>/mark_lost/", views.quote_mark_lost, name="quote_mark_lost"),

    #URL temporal QUITAR
    path("<int:pk>/send/", views.quote_send, name="quote_send"),
] 
