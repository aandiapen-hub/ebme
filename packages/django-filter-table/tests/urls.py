# tests/urls.py

from django.urls import path, include
from .testapp.views import FilteredJobTableView, JobDetailView


urlpatterns = [
    path(
        "",
        include("django_filter_table.urls"),
    ),
    path('jobs/', FilteredJobTableView.as_view(), name='jobs'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job'),
]
