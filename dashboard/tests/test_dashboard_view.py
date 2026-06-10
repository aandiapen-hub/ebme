import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from assets.models import Tblcustomer, AssetView
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.django_db
def test_model_compliance_view_requires_login(client):
    url = reverse('dashboards:model_compliance')
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login page  
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_compliance_view_requires_permission(client, user_setup):
    url = reverse('dashboards:model_compliance')
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Forbidden if user does not have permission

@pytest.mark.django_db
def test_model_compliance_view_renders(client, user, customer, assets):
    url = reverse('dashboards:model_compliance')
    customer = customer()
    assets = assets(count=200, customerid=customer)
    user = user()
    user.customerid = customer
    user.save()

    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200

    #test htmx
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200

@pytest.mark.django_db
def test_asset_compliance_view_requires_login(client):
    url = reverse('dashboards:asset_compliance')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_asset_compliance_view_requires_permission(client, user_setup):
    url = reverse('dashboards:asset_compliance')
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 # Forbidden if user does not have permission 

@pytest.mark.django_db
def test_asset_compliance_view_renders(client, user,assets, jobs, customer):
    url = reverse('dashboards:asset_compliance')
    customer = customer()
    
    assets = assets(count=50)
    for asset in assets:
        asset_jobs = jobs(count=4, assetid=asset)

    user = user()
    user.is_staff=True
    user.save()

    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'dashboards/partials/asset_overall_compliance.html' )

@pytest.mark.django_db
def test_open_jobs_view_requires_login(client):
    url = reverse('dashboards:open_jobs')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_open_jobs_view_requires_permission(client, user_setup):
    url = reverse('dashboards:open_jobs')
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 # Forbidden if user does not have permission

@pytest.mark.django_db
def test_open_jobs_view_renders(client, user, assets, jobs):
    url = reverse('dashboards:open_jobs')
    
    assets = assets(count=50)
    for asset in assets:
        asset_jobs = jobs(count=4, assetid=asset)

    user = user()
    user.is_staff=True
    user.save()

    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'dashboards/partials/open_jobs.html')
