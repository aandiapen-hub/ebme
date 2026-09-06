from urllib.parse import urlencode

from .testapp.models import Tblassets
import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission


@pytest.mark.django_db
def test_htmx_select_view_requires_login(
    client,
):
    url = reverse("assets:assets_list")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_htmx_select_view_renders_for_staff(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=10)

    user = user_setup
    user.is_staff = True 
    user.save()

    client.force_login(user)
    url = reverse(
        "django_filter_table:htmx_picker_search",
        kwargs={
            "modelpath": (
                f"assets__Tblassets"
            ),
            'fieldname': 'serialnumber'
        },
    )
    response = client.get(url)

    options = response.context['options']
    assert len(options) == 20

@pytest.mark.django_db
def test_htmx_select_view_renders_for_non_staff(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=10)

    user = user_setup
    user.is_staff = False
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.customerid = customer1
    user.save()

    client.force_login(user)
    url = reverse(
        "django_filter_table:htmx_picker_search",
        kwargs={
            "modelpath": (
                f"assets__Tblassets"
            ),
            'fieldname': 'serialnumber'
        },
    )
    response = client.get(url)

    options = response.context['options']
    assert len(options) == 10


@pytest.mark.django_db
def test_htmx_select_view_renders_for_fk(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=10)

    user = user_setup
    user.is_staff = True 
    user.save()

    client.force_login(user)
    url = reverse(
        "django_filter_table:htmx_picker_search",
        kwargs={
            "modelpath": (
                f"assets__Tblassets"
            ),
            'fieldname': 'modelid'
        },
    )
    response = client.get(url)

    modelids = set(Tblassets.objects.all().values_list('modelid', flat=True))

    options = response.context['options']
    assert len(modelids) ==  len(options)


@pytest.mark.django_db
def test_htmx_select_view_renders_fk_with_search_q(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=10)

    user = user_setup
    user.is_staff = True 
    user.save()

    client.force_login(user)
    search_q = 'a'
    base_url = reverse(
        "django_filter_table:htmx_picker_search",
        kwargs={
            "modelpath": (
                f"assets__Tblassets"
            ),
            'fieldname': 'modelid'
        },
    )
    qp = urlencode({'q':search_q})
    url = f'{base_url}?{qp}'
    response = client.get(url)


    options = response.context['options']
    assert len(options) <= 20


@pytest.mark.django_db
def test_htmx_select_view_renders_char_with_search_q(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=10)

    user = user_setup
    user.is_staff = True 
    user.save()

    client.force_login(user)
    search_q = 'a'
    base_url = reverse(
        "django_filter_table:htmx_picker_search",
        kwargs={
            "modelpath": (
                f"assets__Tblassets"
            ),
            'fieldname': 'serialnumber'
        },
    )
    qp = urlencode({
        'q':search_q,
        'serialnumber': assets1[0].serialnumber,
    })
    url = f'{base_url}?{qp}'
    response = client.get(url)


    options = response.context['options']
    
    assert len(options) < 20


@pytest.mark.django_db
def test_htmx_select_view_renders_with_selected(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=10)

    user = user_setup
    user.is_staff = True 
    user.save()

    client.force_login(user)
    search_q = 'a'
    base_url = reverse(
        "django_filter_table:htmx_picker_search",
        kwargs={
            "modelpath": (
                f"assets__Tblassets"
            ),
            'fieldname': 'serialnumber'
        },
    )
    qp = urlencode({
        'q':search_q,
        'serialnumber': assets1[0].serialnumber,
        'fieldname':'serialnumber'
    })
    url = f'{base_url}?{qp}'
    response = client.get(url)

    assert str(assets1[0].serialnumber) in response.context['selected']
    
