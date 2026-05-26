import pytest
from django.test import RequestFactory
from django.views.generic import ListView, DetailView
from django.db.models import Q


from django.core.exceptions import PermissionDenied

from documents.models import DocumentsView, TblDocumentLinks
from assets.models import (Tbljob, Tblcustomer)


#create dummy detail view 

