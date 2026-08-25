from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from accounts.forms import SignupForm


def signup(request: HttpRequest) -> HttpResponse:
    """Register a customer account and sign them straight in."""
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'auth/signup.html', {'form': form})
