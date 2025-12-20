
import pytest
from django.test import RequestFactory
from django.views.generic import ListView, DetailView
from django.db.models import Q

from django.core.exceptions import PermissionDenied
from assets.models import Tblassets, Tblcustomer

from assets.mixins import CustomerAssetPermissionMixin

from django.http import Http404

class DummyListView(CustomerAssetPermissionMixin, ListView):
    model = Tblassets

@pytest.mark.django_db
def test_customer_asse_permission_mixin_list(user_setup):
    user = user_setup

    customer = Tblassets.objects.last().customerid

    customer_assets = Tblassets.objects.filter(customerid=customer)
    other_assets = Tblassets.objects.filter(~Q(customerid=customer))
    
    request = RequestFactory().get('/fake-url/')
    request.user = user

    view = DummyListView()
    view.request = request
    
    #test output for user with no customer set
    with pytest.raises(PermissionDenied):
        view.get_queryset()
    
    #test output that user can only see asset that belongs to them
    user.customerid = customer
    qs = view.get_queryset()
    assert set(qs) == set(customer_assets)
    assert any(item in set(qs) for item in set(other_assets)) == False

def test_customer_asse_permission_mixin_list_for_staff(user_setup):
    user = user_setup
    user.is_staff = True
    
    request = RequestFactory().get('/fake-url/')
    request.user = user

    view = DummyListView()
    view.request = request
    
    #test output that user can only see asset that belongs to them
    qs = view.get_queryset()
    assert qs.count() == Tblassets.objects.all().count() 


class DummyDetailView(CustomerAssetPermissionMixin, DetailView):
    model = Tblassets

@pytest.mark.django_db
def test_customer_asset_permission_mixin_object(user_setup):
    user = user_setup

    customer = Tblassets.objects.last().customerid
    pk = Tblassets.objects.last().assetid

    customer_assets = Tblassets.objects.filter(customerid=customer)
    other_assets = Tblassets.objects.filter(~Q(customerid=customer))    
    request = RequestFactory().get('/fake-url/')
    request.user = user
    
    #test user can see thier asset
    view = DummyDetailView()
    view.request = request
    view.kwargs = {'pk':pk}
    with pytest.raises(PermissionDenied):
        view.get_object()
    
    user.customerid = customer
    object = view.get_object()

    assert object in set(customer_assets)

@pytest.mark.django_db
def test_customer_asset_permission_mixin_object_for_staff(user_setup):
    user = user_setup
    user.is_staff = True

    pk = Tblassets.objects.last().assetid

    request = RequestFactory().get('/fake-url/')
    request.user = user
    
    #test user can see thier asset
    view = DummyDetailView()
    view.request = request
    view.kwargs = {'pk':pk}
    

    object = view.get_object()

    assert object

@pytest.mark.django_db
def test_customer_asset_permission_mixin_other_object(user_setup):
    user = user_setup
    customer = Tblassets.objects.last().customerid      
    user.customerid = customer

    other_assets = Tblassets.objects.filter(~Q(customerid=customer))    
    pk = other_assets.last().assetid

    request = RequestFactory().get('/fake-url/')
    request.user = user
    
    #test user can see thier asset
    view = DummyDetailView()
    view.request = request
    view.kwargs = {'pk': pk}

    with pytest.raises(Http404):
        view.get_object()
    


class DummyDetailView2(CustomerAssetPermissionMixin, DetailView):
    model = Tblassets
    
    def get_queryset(self):
        return Tblassets.objects.all()

@pytest.mark.django_db
def test_customer_asset_permission_mixin_other_denied(user_setup):
    user = user_setup
    customer = Tblassets.objects.last().customerid      
    user.customerid = customer

    other_assets = Tblassets.objects.filter(~Q(customerid=customer))    
    pk = other_assets.last().assetid

    request = RequestFactory().get('/fake-url/')
    request.user = user
    
    #test user can see thier asset
    view = DummyDetailView2()
    view.request = request
    view.kwargs = {'pk': pk}

    with pytest.raises(PermissionDenied):
        view.get_object()