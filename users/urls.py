from django.urls import path
from .views import (
    CustomLoginView,
    CustomLogoutView,
    PasswordChangeView,
    LogOutConfirmationView,
    LandingView,
    ColumnChooser,
)

app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('landing/', LandingView.as_view(), name='landing'),
    path('logout/', LogOutConfirmationView.as_view(), name='logout'),
    path('logoutconfirm/', CustomLogoutView.as_view(), name='logout_confirmation'),
    path('update_password/', PasswordChangeView.as_view(), name='update_password'),

    # table column chooser
    path('assets_columns_chooser/', ColumnChooser.as_view(), name='column_chooser'),
]
