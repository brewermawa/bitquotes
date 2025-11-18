from django.urls import path

from . import views

app_name = "quotes"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("list/", views.quote_list, name="quote_list"),
    path("new/", views.QuoteCreateView.as_view(), name="quote_create"),
    path("<int:pk>/", views.dashboard, name="quote_detail"),
    path("<int:pk>/edit", views.dashboard, name="quote_edit"),
    path("load-users-htmx/", views.load_users_htmx, name="load_users_htmx"),
]
