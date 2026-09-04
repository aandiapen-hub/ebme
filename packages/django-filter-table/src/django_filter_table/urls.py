from django.urls import path
from .views import HtmxPickerSearch

from .views import ColumnChooser

app_name = 'django_filter_table'

urlpatterns = [
    # table column chooser
    path('assets_columns_chooser/', ColumnChooser.as_view(), name='column_chooser'),
    path('htmx_search/<str:modelpath>/<str:fieldname>/', HtmxPickerSearch.as_view(), name='htmx_picker_search'),

]
