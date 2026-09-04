from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy

from django.views.generic import TemplateView

# Create your views here.


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('users:landing')


class LogOutConfirmationView(TemplateView):
    template_name = "users/logout.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')


class PasswordUpdateView(PasswordChangeView):
    pass


class LandingView(TemplateView):
    template_name = "users/landing_page.html"


