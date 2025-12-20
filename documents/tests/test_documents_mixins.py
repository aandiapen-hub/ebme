import pytest
from django.test import RequestFactory
from django.views.generic import ListView, CreateView, DetailView
from django.db.models import Q


from django.core.exceptions import PermissionDenied

from documents.models import DocumentsView, TblDocumentLinks
from assets.models import (Tblassets,
                           Tbljob,
                           Tblcustomer)

from documents.mixins import DocumentPermissionMixin

#create dummy view to test mixin

class DummyDocumentList(DocumentPermissionMixin,ListView):
    model = DocumentsView

    permission_required = ''  # or any dummy string

    def has_permission(self):
        return True

#test unknown user cannot see any document list

@pytest.mark.django_db()
def test_document_permission_mixin_unknown_user(user_setup):
    user = user_setup

    request = RequestFactory().get('fake-url')
    request.user = user

    view = DummyDocumentList()
    view.request = request
    view.kwargs = {}

    qs = view.get_queryset()
    assert not qs

#test known user can see their document list
@pytest.mark.django_db()
def test_document_permission_mixin_known_user(user_setup):
    user = user_setup
    customer = Tblcustomer.objects.get(customerid=6)
    user.customerid = customer

    request = RequestFactory().get('fake-url')
    request.user = user

    view = DummyDocumentList()
    view.request = request
    view.kwargs = {}

    qs = view.get_queryset()
    assert qs
    jobs = (set(qs.filter(link_table='1').values_list('link_row',flat=True)))

    qs_customers = set(Tbljob.objects.filter(jobid__in=jobs).values_list('assetid__customerid',flat=True))
    assert len(qs_customers) == 1
    assert customer.customerid in qs_customers

#test known user cannot retrieve other customer documents via linked records
@pytest.mark.django_db()
def test_document_permission_mixin_other_user_retrieve_documentref_denied(user_setup):
    document = DocumentsView.objects.filter(customerid=Tblcustomer.objects.first()).first()
    
    user = user_setup
    user.customerid = Tblcustomer.objects.filter(~Q(customerid=document.customerid.customerid)).first()


    request = RequestFactory().get('fake-url', data={
        'link_row': document.link_row,
        'link_table': document.link_table.table_id
    })

    request.user = user
    
    view = DummyDocumentList()
    view.request = request
    view.kwargs = {}


    with pytest.raises(PermissionDenied):
        view.check_object_permissions(obj=None)


#test known user cannot retrieve other customer documents via pk
@pytest.mark.django_db()
def test_document_permission_mixin_other_user_retrieve_pk_denied(user_setup):
    document = DocumentsView.objects.filter(customerid=Tblcustomer.objects.first()).first()

    
    user = user_setup
    user.customerid = Tblcustomer.objects.filter(~Q(customerid=document.customerid.customerid)).first()

    request = RequestFactory().get('fake-url', data={
        'link_row': document.link_row,
        'link_table': document.link_table.table_id
    })

    request.user = user
    
    view = DummyDocumentList()
    view.request = request
    view.kwargs = {}


    with pytest.raises(PermissionDenied):
        view.check_object_permissions(obj=document)


#test staff can access all documents

@pytest.mark.django_db()
def test_document_permission_mixin_staff_list_access_granted(user_setup):
    user = user_setup
    user.is_staff = True
    request = RequestFactory().get('fake-url')
    request.user = user

    view = DummyDocumentList()
    view.request = request
    view.kwargs = {}

    qs = view.get_queryset()
    assert qs

    assert len(qs) == len(TblDocumentLinks.objects.all())




#create dummy detail view 

class DummyDocumentDetailView(DocumentPermissionMixin,DetailView):
    model = DocumentsView

    permission_required = ''  # or any dummy string

    def get_queryset(self):
        return DocumentsView.objects.all()

    def has_permission(self):
        return True

#test unknown user cannot see any document
@pytest.mark.django_db()
def test_document_permission_mixin_unknown_user_denied(user_setup):
    document = DocumentsView.objects.first()
    user = user_setup


    request = RequestFactory().get('fake-url')
    request.user = user
    
    view = DummyDocumentDetailView()
    view.request = request
    view.kwargs = {'pk':document.document_link_id}


    with pytest.raises(PermissionDenied):
        view.get_object()

#test known user cannot see other customer document
@pytest.mark.django_db()
def test_document_permission_mixin_other_user_denied(user_setup):
    document = DocumentsView.objects.filter(customerid=Tblcustomer.objects.first()).first()
    document_customer = document.customerid

    user = user_setup
    user.customerid = Tblcustomer.objects.filter(~Q(customerid=document_customer.customerid)).first()
    user.save()

    request = RequestFactory().get('fake-url')
    request.user = user
    
    view = DummyDocumentDetailView()
    view.request = request
    view.kwargs = {'pk':document.document_link_id}


    with pytest.raises(PermissionDenied):
        view.get_object()


#test known can retrieve their documents via pk
@pytest.mark.django_db()
def test_document_permission_mixin_other_user_retrieve_pk_success(user_setup):

    document = DocumentsView.objects.filter(customerid=Tblcustomer.objects.first()).first()
    
    user = user_setup
    
    user.customerid = document.customerid
    user.save()

    request = RequestFactory().get('fake-url')

    request.user = user
    
    view = DummyDocumentDetailView()
    view.request = request
    view.kwargs = {'pk':document.document_link_id}


    assert view.get_object()

#test staff can access any documents

@pytest.mark.django_db()
def test_document_permission_mixin_staff_detail_access_granted(user_setup):
    user = user_setup
    user.is_staff = True
    request = RequestFactory().get('fake-url')
    request.user = user

    view = DummyDocumentDetailView()
    view.request = request
    view.kwargs = {}

    document = DocumentsView.objects.first()

    view.kwargs = {'pk':document.document_link_id}
    assert view.get_object()
