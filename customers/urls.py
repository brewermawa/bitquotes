from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="customer_list"),
    path("partial/", views.CustomerListPartialView.as_view(), name="customer_list_partial"),
    path("new/", views.CustomerCreateView.as_view(), name="new_customer"),


    #Rutas para la edición de cliente
    path("<int:pk>/row/edit/", views.customer_row_edit, name="customer_row_partial"),
    path("<int:pk>/row/readonly/", views.customer_row_readonly, name="customer_row_readonly"),
    path("<int:pk>/row/update/", views.customer_row_update, name="customer_row_update"),
]
