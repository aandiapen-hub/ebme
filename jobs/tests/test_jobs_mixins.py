
import pytest
from django.test import RequestFactory
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Q

from django.core.exceptions import PermissionDenied
from assets.models import Tbljob, Tblcustomer, Tblassets,Tbltestscarriedout

from jobs.mixins import (CustomerJobChildPermissionMixin, CustomerJobPermissionMixin,
                         CustomerJobListPermissionMixin)

from django.http import Http404, HttpResponse

# test CustomerJobPermissionMixin

#create a dummy view to test the mixin
class DummyJobDetailView(CustomerJobPermissionMixin,DetailView):
    model = Tbljob
    permission_required = ''  # or any dummy string

    def has_permission(self):
        return True

#user not linked to a customer cannot see any jobs
@pytest.mark.django_db()
def test_customer_job_permission_mixin_no_object(user_setup):
    user =  user_setup

    request = RequestFactory().get('/fake-url/')
    request.user = user

    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}

    #test unknown user access
    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)


#user cannot see other customer jobs
@pytest.mark.django_db()
def test_customer_job_permission_mixin_denied(user_setup):
    user =  user_setup
    job = Tbljob.objects.last()
    customer = job.assetid.customerid

    request = RequestFactory().get('/fake-url/')
    request.user = user

    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {'pk':job.jobid}

    #test other user access
    user.customerid = Tblcustomer.objects.filter(~Q(customerid=customer.customerid)).last()
    request.user = user

    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)
    
#user cannot see jobs for other customer's asset 
@pytest.mark.django_db()
def test_customer_job_permission_mixin_asset_denied(user_setup):
    user =  user_setup
    asset = Tblassets.objects.last()
    customer = asset.customerid
    #set user a customer id different from the selected asset
    user.customerid = Tblcustomer.objects.filter(~Q(customerid=customer.customerid)).last()
    user.save()

    request = RequestFactory().get('/fake-url/',data={'assetid':asset.assetid})
    request.user = user

    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}

    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)
    #test asset does not exist
    request = RequestFactory().get('/fake-url/',data={'assetid':'1000'})
    request.user = user
    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}
    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)

#user cannot see jobs for their asset
@pytest.mark.django_db()
def test_customer_job_permission_mixin_job_denied(user_setup):
    user =  user_setup
    job = Tbljob.objects.last()
    customer = job.assetid.customerid
    user.customerid = Tblcustomer.objects.filter(~Q(customerid=customer.customerid)).last()
    user.save()

    request = RequestFactory().get('/fake-url/',data={'jobid':job.jobid})
    request.user = user
    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}
    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)


    #test job does not exit
    request = RequestFactory().get('/fake-url/',data={'jobid':job.jobid+1})
    request.user = user
    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}
    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)

#user cannot see jobs for their asset
@pytest.mark.django_db()
def test_customer_job_permission_mixin_empty_query_set(user_setup):
    user =  user_setup
    user.save()

    request = RequestFactory().get('/fake-url/')
    request.user = user
    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}
    assert not view.get_queryset()

#test staff can access job from all customer
@pytest.mark.django_db()
def test_staff_can_access_any_job(user_setup):
    user = user_setup
    user.is_staff = True
    user.save()
    job = Tbljob.objects.last()

    request = RequestFactory().get('/fake-url/')
    request.user = user

    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {'pk':job.jobid}
    
    response = view.dispatch(request, **view.kwargs)
    assert isinstance(response, HttpResponse)


#create a dummy view to test the mixin
class DummyJobCreateView(CustomerJobPermissionMixin,CreateView):
    model = Tbljob
    permission_required = ''  # or any dummy string
    fields = '__all__'


    def has_permission(self):
        return True

#asset does not exist
@pytest.mark.django_db()
def test_customer_job_permission_mixin_invalid_asset(user_setup):
    user =  user_setup
    
    job = Tbljob.objects.last()
    customer = job.assetid.customerid
    user.customerid = customer
    user.save()

    request = RequestFactory().get('/fake-url/')
    request.user = user
    view = DummyJobCreateView()
    view.request = request
    view.kwargs = {}
    view.request.GET = {'assetid': "56699874455662"}  # Key part for create view
    with pytest.raises(PermissionDenied):
        view.dispatch(request)


#user cannot see jobs for their asset
@pytest.mark.django_db()
def test_customer_job_permission_mixin_querset_contains_one_customer(user_setup):
    user =  user_setup
    customer = Tblcustomer.objects.last()
    user.customerid = customer
    user.save()

    request = RequestFactory().get('/fake-url/')
    request.user = user
    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {}
    assert view.get_queryset()
    assert len(set(view.get_queryset().values_list('assetid__customerid',flat=True))) ==1


#user can see job linked to their asset
@pytest.mark.django_db()
def test_customer_job_permission_mixin_access_granted(user_setup):
    user =  user_setup
    job = Tbljob.objects.last()
    customer = job.assetid.customerid
    user.customerid = customer
    user.save()

    request = RequestFactory().get('/fake-url/')
    request.user = user

    view = DummyJobDetailView()
    view.request = request
    view.kwargs = {'pk':job.jobid}

    
    response = view.dispatch(request, **view.kwargs)
    assert isinstance(response, HttpResponse)

#test staff can access job from all customer
@pytest.mark.django_db()
def test_staff_can_access_any_asset(user_setup):
    user = user_setup
    user.is_staff = True
    user.save()
    asset = Tblassets.objects.last()

    request = RequestFactory().get(f'/fake-url/?assetid={asset.assetid}')
    request.user = user

    view = DummyJobCreateView()
    view.request = request
    view.kwargs={}
    
    response = view.dispatch(request, **view.kwargs)
    assert isinstance(response, HttpResponse)



# test CustomerJobChildPermissionMixin,

#create a dummy view to test the mixin
class DummyJobChildDetailView(CustomerJobChildPermissionMixin,DetailView):
    model = Tbltestscarriedout
    permission_required = ''  # or any dummy string

    def has_permission(self):
        return True

#test user not linked to any customer cannot access job children
@pytest.mark.django_db()
def test_job_child_permission_unknown_user_denied(user_setup):
    user = user_setup
    test = Tbltestscarriedout.objects.first()
    
    request = RequestFactory().get('/fake-url/',data={'jobid':0})
    request.user = user

    view = DummyJobChildDetailView()
    view.request = request
    view.kwargs = {'pk':test.pk}

    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)

#test user cannot see other customer's job
@pytest.mark.django_db()
def test_job_child_permission_wrong_customer_denied(user_setup):
    user = user_setup
    customer = Tblcustomer.objects.last()
    user.customerid = customer
    

    job = Tbljob.objects.filter(~Q(assetid__customerid=customer.customerid)).last()

    request = RequestFactory().get('/fake-url/', data={'jobid':job.jobid})
    request.user = user

    view = DummyJobChildDetailView()
    view.request = request
    view.kwargs = {'pk':job.jobid}

    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)

#test user can see their job's children records
@pytest.mark.django_db()
def test_job_child_permission_granted(user_setup):
    test = Tbltestscarriedout.objects.last()
    customer = test.jobid.assetid.customerid

    user = user_setup
    user.customerid = customer
    user.save()

    request = RequestFactory().get('/fake-url/', data={'jobid':test.jobid.jobid})
    request.user = user

    view = DummyJobChildDetailView()
    view.request = request
    view.kwargs = {'pk':test.testid}

    
    response = view.dispatch(request, **view.kwargs)
    assert isinstance(response, HttpResponse)

#test job does not exist throws and error
@pytest.mark.django_db()
def test_job_child_job_does_not_exist(user_setup):
    user = user_setup
    customer = Tblcustomer.objects.last()
    user.customerid = customer
    

    job = Tbljob.objects.last()
    test = Tbltestscarriedout.objects.filter(jobid=job.jobid).last()

    request = RequestFactory().get('/fake-url/', data={'jobid':job.jobid+1})
    request.user = user

    view = DummyJobChildDetailView()
    view.request = request
    view.kwargs = {'pk':test.testid}

    with pytest.raises(PermissionDenied):
        view.dispatch(request, **view.kwargs)

#test staff user can see child records of all jobs
@pytest.mark.django_db()
def test_job_child_permission_granted_to_staff(user_setup):
    test = Tbltestscarriedout.objects.last()
    customer = test.jobid.assetid.customerid

    user = user_setup
    user.is_staff = True
    user.save()

    request = RequestFactory().get('/fake-url/', data={'jobid':test.jobid.jobid})
    request.user = user

    view = DummyJobChildDetailView()
    view.request = request
    view.kwargs = {'pk':test.testid}

    
    response = view.dispatch(request, **view.kwargs)
    assert isinstance(response, HttpResponse)


# test CustomerJobListPermissionMixin
#create a dummy view to test the mixin
class DummyJobListView(CustomerJobListPermissionMixin,ListView):
    model = Tbljob
    permission_required = ''  # or any dummy string

    def has_permission(self):
        return True

#test user not linked to any customer cannot see any job
@pytest.mark.django_db()
def test_customer_job_list_permission_view_mixin_unkown_user(user_setup):
    user = user_setup
    
    request = RequestFactory().get('/fake-url/',data={'jobid':0})
    request.user = user

    view = DummyJobListView()
    view.request = request
    view.kwargs = {}

    assert not view.get_queryset()

#test user can see a list of their jobs
@pytest.mark.django_db()
def test_customer_job_list_permission_view_mixin_access_granted(user_setup):
    user = user_setup
    customer = Tblcustomer.objects.last()
    user.customerid = customer
    request = RequestFactory().get('/fake-url/',data={'jobid':0})
    request.user = user

    view = DummyJobListView()
    view.request = request
    view.kwargs = {}

    qs = view.get_queryset()
    assert  len(set(qs.values_list('assetid__customerid',flat=True))) ==1

#test staff can see all customers job list
@pytest.mark.django_db()
def test_staff_access_job_list(user_setup):
    user = user_setup
    user.is_staff=True

    request = RequestFactory().get('/fake-url/',data={'jobid':0})
    request.user = user

    view = DummyJobListView()
    view.request = request
    view.kwargs = {}

    qs = view.get_queryset()
    assert  len(qs) == len(Tbljob.objects.all())