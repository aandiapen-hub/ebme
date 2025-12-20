
from urllib.parse import urlencode
from psycopg import Error
import pytest
from django.db import IntegrityError, transaction, transaction
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed
from assets.models import (Tbljob, Tbljobstatus,
                           Tbltechnicianlist,Tbljobtypes,
                           Tblassets,Tbltestscarriedout,
                           Tblcheckslists,Tbltestresult,
                            Tblpartsused,
                            Tbltesteqused)

from documents.models import TemporaryUpload
from documents.utils import save_extraction_results
import parts
from parts.models import TblPartModel, Tblpartslist
import datetime

from django.contrib.messages import get_messages

from django.core.files import File

# test FilteredJobListView
@pytest.mark.django_db
def test_filtered_job_list_view_requires_login(client):
    url = reverse('jobs:jobs_list')
    response = client.get(url)
    assert response.status_code == 302

@pytest.mark.django_db
def test_filtered_job_list_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('jobs:jobs_list')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])

@pytest.mark.django_db
def test_filtered_job_list_view_renders(client, user_setup, mocker,search_term):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobListPermissionMixin.has_permission', return_value=True)

    client.force_login(user)

    url = reverse('jobs:jobs_list')
    response = client.get(url)
    
    assert response.status_code == 200
    assertTemplateUsed(response, 'jobs/jobs_list.html')

    #test htmx request
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200

    #test with query params
    query_params = urlencode({'universal_search': search_term})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200




#test JobUpdateView
@pytest.mark.django_db
def test_job_update_view_requires_login(client):
    job = Tbljob.objects.last()
    url = reverse('jobs:job_update', kwargs={'pk' : job.jobid})  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_job_udpate_view_permission_denied(client,user_setup):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()

    client.force_login(user)

    url = reverse('jobs:job_update', kwargs={'pk':job.jobid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_update_view_renders(client,user_setup,mocker):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()

    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)

    url = reverse('jobs:job_update', kwargs={'pk':job.jobid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'jobs/update_job.html')



@pytest.mark.django_db
def test_job_update_view_post_successfully(client,user_setup,mocker):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()

    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    url = reverse('jobs:job_update', kwargs={'pk':job.jobid})
    response = client.post(url, data={
        'jobid': job.jobid,
        'jobenddate' :'2025-05-07',
        'jobtypeid': job.jobtypeid.jobtypeid,
        'technicianid': job.technicianid.technicianid,
        'jobstatusid': job.jobstatusid.jobstatusid,
    })

    job.refresh_from_db()
    assert job.jobenddate == datetime.date(2025, 5, 7)
    assert response.status_code == 302
    assert response.url == reverse('jobs:job_summary', kwargs={'pk': job.jobid})



#test JobCreateView

@pytest.mark.django_db
def test_job_create_view_requires_login(client):
    url = reverse('jobs:job_create')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_job_create_view_permission_denied(client,user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('jobs:job_create')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_job_create_view_renders(client,user_setup,mocker):
    asset = Tblassets.objects.last()
    customerid = asset.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)

    url = reverse('jobs:job_create')
    query_params = urlencode({'assetid': asset.assetid})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response.context['assetid'] == str(asset.assetid)

@pytest.mark.django_db
def test_job_create_view_post_successfully(client,user_setup,mocker):
    asset = Tblassets.objects.first()
    user = user_setup
    user.customerid  = asset.customerid

    user.save()
    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)

    url = reverse('jobs:job_create')
    query_params = urlencode({'assetid': asset.assetid})
    full_url = f"{url}?{query_params}"

    form = {
        'assetid': asset.assetid,
        'jobstatusid': Tbljobstatus.objects.last().jobstatusid,
        'technicianid': Tbltechnicianlist.objects.last().technicianid, 
        'jobtypeid': Tbljobtypes.objects.last().jobtypeid,
    }
    response = client.post(full_url,form)
    created_job = Tbljob.objects.last()
    assert created_job.assetid.assetid == asset.assetid
    assert response.status_code == 302
    assert response.url == reverse('jobs:job_update', kwargs={'pk': created_job.jobid})

    #test quick job
    query_params = urlencode({'assetid': asset.assetid,'quickjob':'successful_ppm'})
    full_url = f"{url}?{query_params}"
    
    response = client.post(full_url,form)
    created_job = Tbljob.objects.last()
    assert created_job.assetid.assetid == asset.assetid
    assert response.status_code == 302
    assert response.url == reverse('jobs:job_update', kwargs={'pk': created_job.jobid})

#test JobDeleteView

@pytest.mark.django_db
def test_job_delete_view_requires_login(client):
    job = Tbljob.objects.last()
    url = reverse('jobs:job_delete', kwargs={'pk' : job.jobid})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_job_delete_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    job = Tbljob.objects.last()
    url = reverse('jobs:job_delete', kwargs={'pk' : job.jobid})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_job_delete_view_renders(client,user_setup,mocker):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)

    url = reverse('jobs:job_delete', kwargs={'pk' : job.jobid})
    
    
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['view_type'] == 'delete'
    assert response.context['title'] == f"Delete Job: {job.jobid}"

@pytest.mark.django_db
def test_job_delete_view_post_error(client,user_setup,mocker):
    asset = Tblassets.objects.first()
    user = user_setup
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    
    created_job= Tbljob.objects.create(
        assetid = asset,
        jobstatusid = Tbljobstatus.objects.last(),
        technicianid = Tbltechnicianlist.objects.last(),
        jobtypeid = Tbljobtypes.objects.last(),
    )
    
    Tblpartsused.objects.create(
        jobid = created_job,
        partid = Tblpartslist.objects.last(),
        quantity = 1,
        unitprice = 100
    )


    url = reverse('jobs:job_delete', kwargs={'pk' : created_job.jobid})
    response = client.post(url)
    assert response.status_code == 200
    assert Tbljob.objects.filter(pk=created_job.jobid).exists()

def test_job_delete_view_post_successfully(client,user_setup,mocker):
    asset = Tblassets.objects.first()
    user = user_setup
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    
    created_job= Tbljob.objects.create(
        assetid = asset,
        jobstatusid = Tbljobstatus.objects.last(),
        technicianid = Tbltechnicianlist.objects.last(),
        jobtypeid = Tbljobtypes.objects.last(),
    )
    
    Tbltestscarriedout.objects.filter(jobid=created_job.jobid).delete()



    url = reverse('jobs:job_delete', kwargs={'pk' : created_job.jobid})
    response = client.post(url)
    assert response.status_code == 204
    assert not Tbljob.objects.filter(pk=created_job.jobid).exists()


#test TestcarriedoutListView

@pytest.mark.django_db
def test_tests_carried_out_list_view_requires_login(client):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout')
    query_params = urlencode({'jobid': job.jobid})  # Replace 123 with the actual job ID
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_tests_carried_out_list_view_permission_denied(client,user_setup):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout')
    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"

    user = user_setup
    client.force_login(user)

    response = client.get(full_url)


    assert response.status_code == 403

@pytest.mark.django_db
def test_tests_carried_out_list_view_renders(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout')
    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)

    client.force_login(user)
    
    response = client.get(full_url)


    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/partials/checklist.html")

#test TestcarriedoutUpdateView

@pytest.mark.django_db
def test_tests_carried_out_update_view_requires_login(client):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid

    url = reverse('jobs:testscarriedout_update', kwargs={'pk': testid})
    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_tests_carried_out_update_view_permission_denied(client,user_setup):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid

    url = reverse('jobs:testscarriedout_update', kwargs={'pk': testid})
        
    user = user_setup
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 403

@pytest.mark.django_db
def test_tests_carried_out_update_view_renders(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid

    url = reverse('jobs:testscarriedout_update', kwargs={'pk': testid})
        
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/partials/testscarriedout_update.html")


@pytest.mark.django_db
def test_tests_carried_out_update_view_successful_post(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid

    url = reverse('jobs:testscarriedout_update', kwargs={'pk': testid})
        
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)
    
    data = {'result': 'Fail'}
    response = client.post(url,data=data)
    assert response.status_code == 200
    test.refresh_from_db()
    assert test.resultid.resultname == 'Fail'

@pytest.mark.django_db
def test_tests_carried_out_update_view_successful_post_clear_result(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid

    url = reverse('jobs:testscarriedout_update', kwargs={'pk': testid})

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)
    
    data = {'result': 'Clear'}
    response = client.post(url,data=data)
    assert response.status_code == 200
    test.refresh_from_db()
    assert test.resultid is None

@pytest.mark.django_db
def test_tests_carried_out_update_view_successful_post_htmx(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid

    url = reverse('jobs:testscarriedout_update', kwargs={'pk': testid})
        
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)
    
    data = {'result': 'Fail'}
    response = client.post(url,data=data, HTTP_HX_REQUEST='true' )
    test.refresh_from_db()
    assert test.resultid.resultname == 'Fail'

#test TestscarriedoutCreateView
@pytest.mark.django_db
def test_tests_carried_out_create_view_requires_login(client):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout_create', kwargs={'jobid': job.jobid})
    
    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_tests_carried_out_create_view_permission_denied(client,user_setup):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout_create', kwargs={'jobid': job.jobid})
    
    user = user_setup
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 403

  
def test_tests_carried_out_create_view_renders(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout_create', kwargs={'jobid': job.jobid})
    
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, 'jobs/partials/testscarriedout_modal.html')
    assert response.context['jobid'] == job.jobid

def test_tests_carried_out_create_view_post_successful_htmx(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout_create', kwargs={'jobid': job.jobid})
    
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    Tbltestscarriedout.objects.filter(jobid=job.jobid).delete() # delete all test for this job.

    form = {
       'jobid': job.jobid, 
        'checkid': Tblcheckslists.objects.last().testid,
        'resultid':  Tbltestresult.objects.last().resultid,
    }

    response = client.post(url, form, HTTP_HX_REQUEST='true' )

    assert response.status_code == 200
    testcarriedout = Tbltestscarriedout.objects.last()
    assert testcarriedout.jobid == job


def test_tests_carried_out_create_view_post_successful(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:testscarriedout_create', kwargs={'jobid': job.jobid})
    
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    Tbltestscarriedout.objects.filter(jobid=job.jobid).delete() # delete all test for this job.

    form = {
       'jobid': job.jobid, 
        'checkid': Tblcheckslists.objects.last().testid,
        'resultid':  Tbltestresult.objects.last().resultid,
    }

    response = client.post(url, form )

    assert response.status_code == 302
    testcarriedout = Tbltestscarriedout.objects.last()
    assert testcarriedout.jobid == job

#test_tests_carried_out_delete_view

@pytest.mark.django_db
def test_tests_carried_out_delete_view_requires_login(client):
    job = Tbljob.objects.last()
    test = Tbltestscarriedout.objects.last()
    url = reverse('jobs:testscarriedout_delete', kwargs={'pk': test.testid})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_tests_carried_out_delete_view_permission_denied(client,user_setup):
    job = Tbljob.objects.last()
    test = Tbltestscarriedout.objects.last()
    url = reverse('jobs:testscarriedout_delete', kwargs={'pk': test.testid})
    
    user = user_setup
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 403

@pytest.mark.django_db
def test_tests_carried_out_delete_view_renders(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)

    url = reverse('jobs:testscarriedout_delete', kwargs={'pk': test.testid})
    
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission',return_value=True)
    client.force_login(user)
    
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/partials/testscarriedout_modal.html")
    assert response.context['view_type'] == 'delete'

@pytest.mark.django_db
def test_tests_carried_out_delete_view_successful_post(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid
    
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission',return_value=True)
    client.force_login(user)
    
    url = reverse('jobs:testscarriedout_delete', kwargs={'pk': testid})
    response = client.post(url)

    assert response.status_code == 302
    assert not Tbltestscarriedout.objects.filter(testid=testid).exists()


@pytest.mark.django_db
def test_tests_carried_out_delete_view_successful_post_htmx(client,user_setup,mocker):
    test = Tbltestscarriedout.objects.last()
    jobid = test.jobid.jobid
    job = Tbljob.objects.get(jobid=jobid)
    testid = test.testid
    
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission',return_value=True)
    client.force_login(user)
    
    url = reverse('jobs:testscarriedout_delete', kwargs={'pk': testid})
    response = client.post(url, HTTP_HX_REQUEST='true' )

    assert response.status_code == 200
    assert response.content == b""
    assert not Tbltestscarriedout.objects.filter(testid=testid).exists()


#test_spare_parts_used_create_View
@pytest.mark.django_db
def test_spare_parts_used_create_view_requires_login(client):
    job = Tbljob.objects.last()
    
    url = reverse('jobs:sparepartsused_create', kwargs={'jobid': job.jobid})
    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_spare_parts_used_create_view_permission_denied(client,user_setup):
    job = Tbljob.objects.last()
    url = reverse('jobs:sparepartsused_create', kwargs={'jobid': job.jobid})
    response = client.get(url)
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_spare_parts_used_create_view_renders(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:sparepartsused_create', kwargs={'jobid': job.jobid})
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'jobs/partials/sparepartsused_modal.html')

@pytest.mark.django_db
def test_spare_parts_used_create_view_post_successful(client,user_setup,mocker):
    job = Tbljob.objects.first()
    url = reverse('jobs:sparepartsused_create', kwargs={'jobid': job.jobid})

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    modelid = job.assetid.modelid
    partid = Tblpartslist.objects.last()
    TblPartModel.objects.create(part=partid, model=modelid)
    form = {
       'jobid': job.jobid, 
        'partid': partid.partid,
        'quantity':'2',
        'unitprice':10
    }

    response = client.post(url, form,)

    assert response.status_code == 302

@pytest.mark.django_db
def test_spare_parts_used_create_view_post_successful_htmx(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:sparepartsused_create', kwargs={'jobid': job.jobid})

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    modelid = job.assetid.modelid
    partid = Tblpartslist.objects.last()
    TblPartModel.objects.create(part=partid, model=modelid)
    form = {
       'jobid': job.jobid, 
        'partid': partid.partid,
        'quantity':'2',
        'unitprice':10
    }


    response = client.post(url, form, HTTP_HX_REQUEST='true' )
    assert response.status_code == 200


@pytest.mark.django_db
def test_spare_parts_used_create_view_post_unsuccessful(client,user_setup,mocker):
    job = Tbljob.objects.first()
    url = reverse('jobs:sparepartsused_create', kwargs={'jobid': job.jobid})

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    partid = Tblpartslist.objects.last().partid

    form = {
        'quantity':'-1',
        'unitprice':200
    }

    response = client.post(url, form,)
    assert response.status_code == 200




#test SparePartsUsedListView
@pytest.mark.django_db
def test_spare_parts_used_list_view_requires_login(client):
    job = Tbljob.objects.last()
    
    url = reverse('jobs:sparepartsused')

    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"

    response = client.get(full_url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_spare_parts_used_list_view_permission_denied(client,user_setup):
    job = Tbljob.objects.last()
    url = reverse('jobs:sparepartsused')
    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"
    user = user_setup
    client.force_login(user)
    response = client.get(full_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_parts_used_list_view_renders(client,user_setup,mocker):
    job = Tblpartsused.objects.last().jobid
    
    url = reverse('jobs:sparepartsused')
    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)
    response = client.get(full_url)
    assert response.status_code == 200
    assertTemplateUsed(response,"jobs/partials/partslist.html")

# test SparePartsUsedDetailView
@pytest.mark.django_db
def test_spare_parts_used_detail_view_requires_login(client):
    part_used = Tblpartsused.objects.last()
    job = part_used.jobid
    
    url = reverse('jobs:sparepartsused_detail', kwargs={'pk':part_used.pk})

    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_spare_parts_used_detail_view_permission_denied(client,user_setup):
    part_used = Tblpartsused.objects.last()
    job = part_used.jobid
    
    url = reverse('jobs:sparepartsused_detail', kwargs={'pk':part_used.pk})
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_parts_used_detail_view_renders(client,user_setup,mocker):
    part_used = Tblpartsused.objects.last()
    job = part_used.jobid
    
    url = reverse('jobs:sparepartsused_detail', kwargs={'pk':part_used.pk})
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,"jobs/partials/partslist.html")

    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200


#test_spare_parts_used_update_view
@pytest.mark.django_db
def test_spare_parts_used_update_view_requires_login(client):
    partused = Tblpartsused.objects.last()
    url = reverse('jobs:sparepartsused_update', kwargs={'pk':partused.partsusedid})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_spare_parts_used_update_view_permission_required(client, user_setup):
    partused = Tblpartsused.objects.last()
    client.force_login(user_setup)
    url = reverse('jobs:sparepartsused_update', kwargs={'pk':partused.partsusedid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_parts_used_update_view_renders(client, user_setup, mocker):
    parts_used = Tblpartsused.objects.last()
    job = Tbljob.objects.get(jobid=parts_used.jobid.jobid)
    url = reverse('jobs:sparepartsused_update', kwargs={'pk': parts_used.partsusedid})
    
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/partials/sparepartsused_update.html")

@pytest.mark.django_db
def test_spare_parts_used_update_post_successful(client,user_setup,mocker):
    parts_used = Tblpartsused.objects.last()
    job = Tbljob.objects.get(jobid=parts_used.jobid.jobid)
    url = reverse('jobs:sparepartsused_update', kwargs={'pk': parts_used.partsusedid})


    #test successful submission
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)

    form = {
        'jobid':job.jobid,
        'partid': parts_used.partid.partid,
        'quantity':10,
        'unitprice':201
    }

    response = client.post(url, form,)

    assert response.status_code == 302
    parts_used.refresh_from_db()
    assert parts_used.unitprice == 201

    #test successful htmx

    response = client.post(url, form, HTTP_HX_REQUEST='true')

    assert response.status_code == 200
    parts_used.refresh_from_db()
    assert parts_used.unitprice == 201

@pytest.mark.django_db
def test_spare_parts_used_update_post_unsuccessful(client,user_setup,mocker):
    parts_used = Tblpartsused.objects.last()
    job = Tbljob.objects.get(jobid=parts_used.jobid.jobid)
    url = reverse('jobs:sparepartsused_update', kwargs={'pk': parts_used.partsusedid})


    #test unsuccessful submission
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)

    form = {
        'jobid':parts_used.jobid,
        'partid':parts_used.partid.partid,
        'quantity':-1,
        'unitprice':201
    }

    with pytest.raises(transaction.TransactionManagementError):
        try:
            # Simulate failure: missing required field
            response = client.post(url, form,)
        except IntegrityError:
            # Django marks transaction as broken
            pass

#test_spare_parts_used_delete_view
def test_spare_parts_used_delete_view(client,user_setup,mocker):
    parts_used = Tblpartsused.objects.last()
    parts_used_id = parts_used.partsusedid
    job = Tbljob.objects.get(jobid=parts_used.jobid.jobid)
    url = reverse('jobs:sparepartsused_delete', kwargs={'pk': parts_used_id})

    #test login required mixin
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

    #test permission required mixin
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403
    client.logout()

    #test view renders
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['view_type'] == 'delete'

       
    #test successful submission
    response = client.post(url)

    assert response.status_code == 302
    assert not Tblpartsused.objects.filter(partsusedid=parts_used_id).exists()

def test_spare_parts_used_delete_view_htmx_post(client,user_setup,mocker):
    parts_used = Tblpartsused.objects.last()
    parts_used_id = parts_used.partsusedid
    job = Tbljob.objects.get(jobid=parts_used.jobid.jobid)
    url = reverse('jobs:sparepartsused_delete', kwargs={'pk': parts_used_id})

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)

    client.force_login(user)

    #test successful submission
    response = client.post(url, HTTP_HX_REQUEST='true')

    assert response.status_code == 200
    assert not Tblpartsused.objects.filter(partsusedid=parts_used_id).exists()


#test TestEquipmentUsedView

@pytest.mark.django_db
def test_test_equipment_used_list_view_requires_login(client):
    job = Tbljob.objects.last()
    
    url = reverse('jobs:testequipmentused')

    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"

    response = client.get(full_url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_test_equipment_used_list_view_permission(client,user_setup):
    job = Tbljob.objects.last()
    url = reverse('jobs:testequipmentused')
    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"

    user = user_setup
    client.force_login(user)
    response = client.get(full_url)

    assert response.status_code == 403

@pytest.mark.django_db
def test_test_equipment_used_list_view_renders(client,user_setup,mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:testequipmentused')
    query_params = urlencode({'jobid': job.jobid})  
    full_url = f"{url}?{query_params}"

    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)

    response = client.get(full_url)

    assert response.status_code == 200
    assertTemplateUsed(response, 'jobs/partials/testeqlist.html')
    assert response.context['jobid'] == str(job.jobid)

#test TestEquipmentUsedCreateView

@pytest.mark.django_db
def test_test_equipment_used_create_view_requires_login(client):
    job = Tbljob.objects.last()
    
    url = reverse('jobs:testequipmentused_create',kwargs ={'jobid': job.jobid})
    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_test_equipment_used_create_view_requires_permission(client, user_setup):
    job = Tbljob.objects.last()
    url = reverse('jobs:testequipmentused_create',kwargs ={'jobid': job.jobid})
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_test_equipment_used_create_view_renders(client, user_setup, mocker):
    job = Tbljob.objects.last()
    url = reverse('jobs:testequipmentused_create',kwargs ={'jobid': job.jobid})
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)


    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'jobs/partials/testeqused_modal.html')
    assert response.context['jobid'] == job.jobid

@pytest.mark.django_db
def test_test_equipment_used_create_view_post(client, user_setup, mocker):
    job = Tbljob.objects.first()
    url = reverse('jobs:testequipmentused_create',kwargs ={'jobid': job.jobid})
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    form = {
            'jobid': job.jobid,
            'test_eq':Tblassets.objects.filter(is_test_eq=True).first().assetid
    }

    response = client.post(url, form,)
    assert response.status_code == 302


#test TestEquipmentUsedDeleteView
@pytest.mark.django_db
def test_test_equipment_used_delete_view_requires_login(client):
    testeqused = Tbltesteqused.objects.last()
    jobid = testeqused.jobid

    url = reverse('jobs:testequipmentused_delete',kwargs ={'pk': testeqused.id })
    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_test_equipment_used_delete_view_requires_permission(client,user_setup):
    testeqused = Tbltesteqused.objects.last()
    job = testeqused.jobid
    url = reverse('jobs:testequipmentused_delete',kwargs ={'pk': testeqused.id })
    
    user = user_setup
    user.customerid = Tbljob.objects.get(jobid=job.jobid).assetid.customerid
    user.save()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_test_equipment_used_delete_view_renders(client,user_setup,mocker):
    testeqused = Tbltesteqused.objects.last()
    job = testeqused.jobid
    url = reverse('jobs:testequipmentused_delete',kwargs ={'pk': testeqused.id })
    
    user = user_setup
    user.customerid = Tbljob.objects.get(jobid=job.jobid).assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'jobs/partials/testeqused_delete_modal.html')

@pytest.mark.django_db
def test_test_equipment_used_delete_view_post_successful(client,user_setup,mocker):
    testeqused = Tbltesteqused.objects.last()
    testid = testeqused.id
    job = testeqused.jobid
    url = reverse('jobs:testequipmentused_delete',kwargs ={'pk': testeqused.id })
    
    user = user_setup
    user.customerid = Tbljob.objects.get(jobid=job.jobid).assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302
    assert not  Tbltesteqused.objects.filter(id=testid).exists()

@pytest.mark.django_db
def test_test_equipment_used_delete_view_post_htmx(client,user_setup,mocker):
    testeqused = Tbltesteqused.objects.last()
    testid = testeqused.id
    job = testeqused.jobid
    url = reverse('jobs:testequipmentused_delete',kwargs ={'pk': testeqused.id })
    
    user = user_setup
    user.customerid = Tbljob.objects.get(jobid=job.jobid).assetid.customerid
    user.save()
    mocker.patch('jobs.mixins.CustomerJobChildPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    response = client.post(url,HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert not  Tbltesteqused.objects.filter(id=testid).exists()

#test GenerateJobReportView
@pytest.mark.django_db
def test_generate_job_report_view_requires_login(client):
    url = reverse('jobs:gen_report')
    response = client.get(url)

    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_generate_job_report_view_permission_required (client, user_setup):
    client.force_login(user_setup)
    url = reverse('jobs:gen_report')
    response = client.get(url)

    assert response.status_code == 403

@pytest.mark.django_db
def test_generate_job_report_view_renders(client, user_setup, mocker):
    from assets.models import Tblcustomer
    url = reverse('jobs:gen_report')
    customer = Tblcustomer.objects.get(customerid=6)
    user = user_setup
    user.customerid = customer
    user.save()
    mocker.patch('jobs.mixins.CustomerJobListPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    query_params = urlencode({'customerid':customer.pk, 'report_type':'service_report', 'enddate_min': '2025-04-03'})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'


    query_params = urlencode({'customerid':customer.pk, 'report_type':'job_list', 'enddate_min': '2025-07-03'})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'

@pytest.mark.django_db
def test_generate_job_report_view_renders_for_staff(client, user_setup, mocker):

    url = reverse('jobs:gen_report')
    user = user_setup
    user.is_staff = True
    user.save()

    mocker.patch('jobs.mixins.CustomerJobListPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    query_params = urlencode({'customerid':'1', 'report_type':'service_report', 'enddate_min': '2025-7-03'})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'

@pytest.mark.django_db
def test_generate_job_report_view_renders_error(client, user_setup, mocker):
    from assets.models import Tblcustomer
    url = reverse('jobs:gen_report')
    customer = Tblcustomer.objects.get(customerid=0)
    user = user_setup
    user.customerid = customer
    user.save()
    mocker.patch('jobs.mixins.CustomerJobListPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    full_url = f"{url}"
    response = client.get(full_url)
    assert response.status_code == 400

    #htmx request are redirected to full http

    full_url = f"{url}"
    response = client.get(full_url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200


@pytest.mark.django_db
def test_service_report_reader_requires_login(client):
    url = reverse('jobs:report_scanner', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_service_report_reader_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('jobs:report_scanner', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_service_report_reader_post(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_files','service_report.pdf')

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name=".jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'application/pdf'
        )
    group = image.group
    data = {'group':group}
        
    url = reverse('jobs:report_scanner', kwargs={'temp_file_group':group})
    response = client.post(url,data)
    assert response.status_code == 200
    assert 'report_output' in response['HX-Redirect']


@pytest.mark.django_db
def test_service_report_reader_post_incorrect_file_type(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_files','delivery_note.jpeg')

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name=".jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpeg'
        )
    group = image.group
    data = {'group':group}
        
    url = reverse('jobs:report_scanner', kwargs={'temp_file_group':group})
    response = client.post(url,data)
    assert response.status_code == 200
    
    assertTemplateUsed("partials/messages.html")
    error_messages = list(get_messages(response.wsgi_request))
    assert any(
            "Document does not contain service or calibration data" in str(message) for message in error_messages
    )


@pytest.mark.django_db
def test_service_report_output_requires_login(client):
    url = reverse('jobs:report_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_service_report_output_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('jobs:report_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_service_report_output_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    serialnumber = Tbljob.objects.last().assetid.serialnumber

    save_extraction_results(
        user_id=user,
        group=1,
        results={'serialnumber': serialnumber,
                'workstartdate': '2021-10-21',
                'workenddate': '2021-10-21',
                'workdone' : 'test work done'
                },
        hours=1,
    )


    url = reverse('jobs:report_reader_output', kwargs={'temp_file_group':1})

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'jobs/partials/report_reader_output.html')


@pytest.mark.django_db
def test_job_create_from_report_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    serialnumber = Tbljob.objects.last().assetid.serialnumber

    save_extraction_results(
        user_id=user,
        group=1,
        results={'serialnumber': serialnumber,
                'workstartdate': '2021-10-21',
                'workenddate': '2021-10-21',
                'workdone' : 'test work done'
                },
        hours=1,
    )


    url = reverse('jobs:create_job_from_report', kwargs={'temp_file_group':1})

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'jobs/partials/create_job_from_report.html')


@pytest.mark.django_db
def test_job_create_from_report_view_post(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    asset = Tbljob.objects.last().assetid
    serialnumber = asset.serialnumber

    import os
    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, 'test_files','service_report.pdf')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="service_report.pdf")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'application/pdf'
        )


    save_extraction_results(
        user_id=user,
        group=1,
        results={'serialnumber': serialnumber,
                'workstartdate': '2021-10-21',
                'workenddate': '2021-10-21',
                'workdone' : 'test work done'
                },
        hours=1,
    )

    form = {
        'assetid': asset.assetid,
        'jobstatusid': Tbljobstatus.objects.last().jobstatusid,
        'technicianid': Tbltechnicianlist.objects.last().technicianid, 
        'jobtypeid': Tbljobtypes.objects.last().jobtypeid,
        'group':image.group
    }

    url = reverse('jobs:create_job_from_report', kwargs={'temp_file_group':1})
    response = client.post(url,form)
    assert response.status_code == 200



@pytest.mark.django_db
def test_job_update_from_report_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    
    job = Tbljob.objects.last()
    asset = job.assetid
    serialnumber = asset.serialnumber
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)




    save_extraction_results(
        user_id=user,
        group=1,
        results={'serialnumber': serialnumber,
                'workstartdate': '2021-10-21',
                'workenddate': '2021-10-21',
                'workdone' : 'test work done'
                },
        hours=1,
    )


    url = reverse('jobs:job_update_from_report',kwargs={'pk':job.pk, 'temp_file_group':1})

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'jobs/partials/update_job_from_report.html')


@pytest.mark.django_db
def test_job_update_from_report_view_post(client, user_setup, mocker):
    user = user_setup
    mocker.patch('jobs.mixins.CustomerJobPermissionMixin.has_permission', return_value=True)
    job = Tbljob.objects.last()
    asset = job.assetid
    serialnumber = asset.serialnumber
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)
    
    import os
    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, 'test_files','service_report.pdf')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="service_report.pdf")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'application/pdf'
        )



    save_extraction_results(
        user_id=user,
        group=1,
        results={'serialnumber': serialnumber,
                'workstartdate': '2021-10-21',
                'workenddate': '2021-10-21',
                'workdone' : 'test work done'
                },
        hours=1,
    )

    data={
        'jobid': job.jobid,
        'jobenddate' :'2025-05-07',
        'jobtypeid': job.jobtypeid.jobtypeid,
        'technicianid': job.technicianid.technicianid,
        'jobstatusid': job.jobstatusid.jobstatusid,
        'group': image.group
    }

    url = reverse('jobs:job_update_from_report',kwargs={'pk':job.pk, 'temp_file_group':1})

    response = client.post(url,data)
    assert response.status_code == 302


