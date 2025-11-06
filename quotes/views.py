from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, "quotes/dashboard.html")
