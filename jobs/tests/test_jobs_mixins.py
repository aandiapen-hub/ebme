
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


#test staff can access job from all customer
@pytest.mark.django_db()
def test_staff_can_access_any_asset(
    client,
    user_setup,
    jobs,
):
    jobs = jobs(count=30)

    user = user_setup
    user.is_staff = True
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('jobs:jobs_list') 
    response = client.get(url)
    assert response.context['table'].data.data.count() == 30


#test user not linked to any customer cannot access job children
@pytest.mark.django_db()
def test_job_child_permission_unknown_user_denied(
    client,
    user_setup,
    test_carried_out,
):
    user = user_setup
    test = test_carried_out()
    user.customerid = None

    permission = Permission.objects.get(codename="view_tbltestscarriedout")
    user.user_permissions.add(permission)

    client.force_login(user)
    url = reverse('jobs:testscarriedout_update', kwargs={'pk': test.pk}) 
    response = client.get(url)

    assert response.status_code == 403


#test user cannot see other customer's job child
@pytest.mark.django_db()
def test_job_child_permission_wrong_customer_denied(
    client,
    user_setup,
    test_carried_out,
    customer,
):
    user = user_setup
    test = test_carried_out()
    user.customerid = customer()

    permission = Permission.objects.get(codename="change_tbltestscarriedout")
    user.user_permissions.add(permission)

    client.force_login(user)
    url = reverse('jobs:testscarriedout_update', kwargs={'pk': test.pk}) 
    response = client.get(url)

    assert response.status_code == 403

#test user can see their job's children records
@pytest.mark.django_db()
def test_job_child_permission_granted(
    client,
    user_setup,
    test_carried_out,
):
    user = user_setup
    test = test_carried_out()
    user.customerid = test.jobid.assetid.customerid
    user.save()

    permission = Permission.objects.get(codename="change_tbltestscarriedout")
    user.user_permissions.add(permission)

    client.force_login(user)
    url = reverse('jobs:testscarriedout_update', kwargs={'pk': test.pk}) 
    response = client.get(url)

    assert response.status_code == 200

#test job does not exist throws and error
@pytest.mark.django_db()
def test_job_child_job_does_not_exist(
    client,
    user_setup,
    test_carried_out,
):
    user = user_setup
    test = test_carried_out()
    user.customerid = test.jobid.assetid.customerid

    permission = Permission.objects.get(codename="change_tbltestscarriedout")
    user.user_permissions.add(permission)

    client.force_login(user)
    url = reverse('jobs:testscarriedout_update', kwargs={'pk': test.pk+1}) 
    response = client.get(url)

    assert response.status_code == 403

#test staff user can see child records of all jobs
@pytest.mark.django_db()
def test_job_child_permission_granted_to_staff(
    client,
    user_setup,
    test_carried_out_batch,
):
    user = user_setup
    tests = test_carried_out_batch()
    user.is_staff=True
    user.save()

    permission = Permission.objects.get(codename="change_tbltestscarriedout")
    user.user_permissions.add(permission)

    client.force_login(user)
    url = reverse('jobs:testscarriedout_update', kwargs={'pk': tests[0].pk}) 
    response = client.get(url)

    assert response.status_code == 200


