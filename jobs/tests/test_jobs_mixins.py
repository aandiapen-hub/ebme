
from django.contrib.auth.models import Permission
import pytest
from django.urls import reverse
from assets.models import TblAssetStatus

# test CustomerJobPermissionMixin

#user cannot see other customer jobs
@pytest.mark.django_db()
def test_customer_job_permission_mixin_denied(
    client,
    user_setup,
    job,
    customer
):
    customer1 = customer(customer_name='customerA')
    job = job()

    user = user_setup
    user.customerid = customer1
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('jobs:job_summary', kwargs={'pk':job.pk}) 
    response = client.get(url)
    assert response.status_code == 403


#user cannot see non-existent job 
@pytest.mark.django_db()
def test_customer_job_permission_mixin_asset_denied(
    client,
    user_setup,
    job,
    customer
):
    customer1 = customer(customer_name='customerA')
    job = job()

    user = user_setup
    user.customerid = customer1
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('jobs:job_summary', kwargs={'pk':job.pk}) 
    response = client.get(url)
    assert response.status_code == 403



#test staff can access job from all customer
@pytest.mark.django_db()
def test_staff_can_access_any_job(
    client,
    user_setup,
    jobs,
    customer
):
    jobs = jobs(count=30)

    user = user_setup
    customer = jobs[0].assetid.customerid
    user.customerid = customer
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('jobs:jobs_list') 
    response = client.get(url)
    customer_jobs = [job for job in jobs if job.assetid.customerid==customer]
    assert response.context['table'].data.data.count() == len(customer_jobs) 

