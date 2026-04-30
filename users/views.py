from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import UserProfiles
from django.apps import apps


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


# column chooser

class ColumnChooser(LoginRequiredMixin, TemplateView):
    model = UserProfiles
    template_name = 'users/partials/column_chooser.html'

    def get_success_url(self):
        base_url = reverse(self.request.POST.get("success_url"))
        query_params = self.request.POST.get("query_params",'')
        return f"{base_url}?{query_params}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get user's visible colums if exists
        user = self.request.user
        request_app_model = self.request.GET.get('appmodel')
        model_name = request_app_model.split('.')[1]

        # list available columns
        model = apps.get_model(request_app_model)
        if model:
            available_columns = [field.name for field in model._meta.get_fields() if field.concrete and not field.auto_created]

        profile = UserProfiles.objects.filter(user_id=user).first()
        if profile and model_name:
            visible_columns = profile.get_preference(model_name, 'visible_columns')
            if visible_columns:
                context['visible_columns'] = visible_columns
                available_columns = [f for f in available_columns if f not in visible_columns]

        context["available_columns"] = available_columns

        context['request_model'] = model_name
        context['success_url'] = self.request.GET.get('success_url')
        context["query_params"] = self.request.GET.urlencode()
        return context

    def post(self, request, *args, **kwargs):
        request_model = request.POST.get('request_model')
        user_id = self.request.user
        profile, created = UserProfiles.objects.get_or_create(
            user_id=user_id, defaults={"table_settings": {}}
        )

        columns = request.POST.getlist('columns', None)
        if columns and profile:
            profile.set_preference(request_model, 'visible_columns', columns)
        return HttpResponseRedirect(self.get_success_url())
