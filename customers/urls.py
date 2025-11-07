from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.ClientListView.as_view(), name="customer_list"),
]
