from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="customer_list"),
    path("partial/", views.CustomerListPartialView.as_view(), name="customer_list_partial"),
    path("row/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_row_partial"),
    path("row_readonly/<int:pk>/", views.CustomerListPartialView.as_view(), name="customer_row_readonly"),
    path("row_update/<int:pk>/", views.CustomerListPartialView.as_view(), name="customer_row_update"),
]
