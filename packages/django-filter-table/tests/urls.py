# tests/urls.py

from django.urls import path
from .testapp.views import FilteredJobTableView

urlpatterns = [
    path('jobs/', FilteredJobTableView.as_view(), name='jobs'),
]
