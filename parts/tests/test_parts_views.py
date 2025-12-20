from django.contrib.messages import get_messages
from urllib.parse import urlencode
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from parts.models import Tblpartslist, Tblpartsprice, TblPartModel

from assets.models import Tbljob, Tblmodel, Tblpartsused
from procurement.models import TblSuppliers
from django.db import IntegrityError, transaction
#test parts table view

@pytest.mark.django_db
def test_parts_table_view_requires_login(client):
    url = reverse('parts:parts')
    response = client.get(url)
    assert response.status_code == 302  # Expecting a redirect to the login page if not authenticated
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_parts_table_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:parts')
    response = client.get(url)
    assert response.status_code == 403
    
@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])
@pytest.mark.django_db
def test_parts_table_view_renders(client, user_setup, mocker, search_term):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:parts')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/parts_list.html')
    #test filter
    query_params = urlencode({'universal_search' : search_term})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

    response_htmx = client.get(url_with_params,HTTP_HX_REQUEST='true')
    assert response_htmx.status_code == 200

#test PartUpdateView

@pytest.mark.django_db
def test_part_update_view_login_required(client):
    url = reverse('parts:update_part', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_part_update_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:update_part', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_part_update_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    part = Tblpartslist.objects.last()
    client.force_login(user_setup)
    url = reverse('parts:update_part', kwargs={'pk': part.partid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/partial.html')

@pytest.mark.django_db
def test_part_update_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    part = Tblpartslist.objects.last()
    client.force_login(user_setup)
    url = reverse('parts:update_part', kwargs={'pk': part.partid})
    data = {'short_name': 'Updated Part',
            'description': 'Updated Description',
            'part_id': part.partid,
            'part_number': part.part_number,}
    response = client.post(url, data)
    assert response.status_code == 302

    part.refresh_from_db()
    assert part.short_name == 'Updated Part'

#test PartDeleteView
@pytest.mark.django_db
def test_part_delete_view_login_required(client):
    url = reverse('parts:delete_part', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_part_delete_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:delete_part', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_part_delete_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    part = Tblpartslist.objects.last()
    client.force_login(user_setup)
    url = reverse('parts:delete_part', kwargs={'pk': part.partid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/partial.html')

@pytest.mark.django_db
def test_part_delete_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    Tblpartslist.objects.create(part_number='testpart', supplier_id=TblSuppliers.objects.last())
    part = Tblpartslist.objects.last()
    client.force_login(user_setup)
    url = reverse('parts:delete_part', kwargs={'pk': part.partid})
    response = client.post(url)
    assert response.status_code == 200

    with pytest.raises(Tblpartslist.DoesNotExist):
        part.refresh_from_db()


@pytest.mark.django_db
def test_part_delete_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    part = Tblpartslist.objects.last()
    Tblpartsused.objects.create(
        jobid= Tbljob.objects.last(),
        quantity= 1,
        partid= part 
    )
    client.force_login(user_setup)
    url = reverse('parts:delete_part', kwargs={'pk': part.partid})
    response = client.post(url)
    assert response.status_code == 200

    assert 'An error occurred while' in response.content.decode()


#test PartCreateView
@pytest.mark.django_db
def test_part_create_view_login_required(client):
    url = reverse('parts:create_part')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_part_create_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:create_part')
    response = client.get(url)
    assert response.status_code == 403  

@pytest.mark.django_db
def test_part_create_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:create_part')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/update_part.html')

@pytest.mark.django_db
def test_part_create_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:create_part')
    supplier = TblSuppliers.objects.last()

    data = {
        'short_name': 'New Partsss',
        'description': 'New Description',
        'part_number': '1234567890123sss',
        'inactive': False,
        'supplier_id': supplier.supplier_id
    }
    response = client.post(url, data)
    messages = list(get_messages(response.wsgi_request))
    assert response.status_code == 302
    new_part = Tblpartslist.objects.last()
    assert new_part.part_number == '1234567890123sss'

@pytest.mark.django_db
def test_part_create_view_post_unsuccessful_duplicate_record(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:create_part')
    part = Tblpartslist.objects.last()
    supplier = part.supplier_id
    part_number = part.part_number
    data = {
        'short_name': 'New',
        'description': 'New Description',
        'part_number': part.part_number,
        'inactive': False,
        'supplier_id': supplier.supplier_id
    }
    with pytest.raises(transaction.TransactionManagementError):
            # Simulate failure: duplicate part number
            response = client.post(url, data)

            messages = [m.message for m in get_messages(response.wsgi_request)]
            assert 'already exists' in messages


    

@pytest.mark.django_db
def test_part_create_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:create_part')
    supplier = TblSuppliers.objects.last()

    data = {
        'short_name': 'New Partsss',
        'description': 'New Description',
        'part_number': '1234567890123sss',
        'inactive': False,
        'supplier_id': supplier.supplier_id
    }
    response = client.post(url, data)

    with pytest.raises(Exception):
        try:
            # Simulate failure: missing required field
            response2=client.post(url, data)

        except IntegrityError:
            messages = [m.message for m in get_messages(response2.wsgi_request)]
            assert 'unique_part' in messages
            # Django marks transaction as broken
            pass



#test Spare Parts Price List View
@pytest.mark.django_db
def test_spare_part_price_list_view_requires_login(client):
    url = reverse('parts:part_prices')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_spare_part_price_list_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:part_prices')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_spare_part_price_list_view_renders(client, user_setup, mocker):

    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:part_prices')
    query_params = urlencode({'partid': 0})
    #test response with partid
    response = client.get(f"{url}?{query_params}")
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/part_prices.html')

    #test response without partid
    response = client.get(url)
    assert response.status_code == 200




#test_SparePartPriceCreateView
@pytest.mark.django_db
def test_spare_part_price_create_view_login_required(client):
    url = reverse('parts:part_prices_create')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_spare_part_prices_create_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:part_prices_create')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_spare_part_prices_create_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:part_prices_create')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/part_prices_create.html")

@pytest.mark.django_db
def test_spare_part_prices_create_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:part_prices_create')
    data = {
        'partid': 1,
        'price': 100.00,
        'effectivedate': '2023-10-01',
    }
    response = client.post(url, data)
    
    assert response.status_code == 302

    # Check if the price was created
    from parts.models import Tblpartsprice
    new_price = Tblpartsprice.objects.last()
    assert new_price.price == 100.00

@pytest.mark.django_db
def test_spare_part_prices_create_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:part_prices_create')
    data = {
        'partid': 1,
        'price': -100.00,
        'effectivedate': '2023-10-01',
    }
    

    with pytest.raises(transaction.TransactionManagementError):
        try:
            # Simulate failure: missing required field
            response=client.post(url, data)

        except IntegrityError:
            messages = [m.message for m in get_messages(response.wsgi_request)]
            assert 'valid_price' in messages
            # Django marks transaction as broken
            pass




#test SparePartPriceDeleteView
@pytest.mark.django_db
def test_spare_part_price_delete_view_login_required(client):
    url = reverse('parts:part_prices_delete', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_spare_part_price_delete_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:part_prices_delete', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_spare_part_price_delete_view_renders(client, user_setup, mocker):
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.first(), price=50.00, effectivedate='2023-10-01'    )
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    price = Tblpartsprice.objects.last()
    url = reverse('parts:part_prices_delete', kwargs={'pk': price.priceid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/part_prices_delete.html')

@pytest.mark.django_db
def test_spare_part_price_delete_view_post_successfull(client, user_setup, mocker):
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.first(), price=50.00, effectivedate='2023-10-01')
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.first(), price=90.00, effectivedate='2024-10-01')
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    price = Tblpartsprice.objects.last()
    url = reverse('parts:part_prices_delete', kwargs={'pk': price.priceid})
    response = client.post(url)
    
    assert response.status_code == 302

    with pytest.raises(Tblpartsprice.DoesNotExist):
        price.refresh_from_db()

@pytest.mark.django_db
def test_spare_part_price_delete_view_post_htmx_successfull(client, user_setup, mocker):
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.first(), price=50.00, effectivedate='2020-10-01')
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.first(), price=90.00, effectivedate='2021-10-01')
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    price = Tblpartsprice.objects.last()
    url = reverse('parts:part_prices_delete', kwargs={'pk': price.priceid})
    response = client.post(url, HTTP_HX_REQUEST='true')
    
    assert response.status_code == 200

    with pytest.raises(Tblpartsprice.DoesNotExist):
        price.refresh_from_db()






#test SparePartPriceUpdateView
@pytest.mark.django_db
def test_spare_part_price_update_view_login_required(client):
    url = reverse('parts:part_prices_update', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_spare_part_price_update_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:part_prices_update', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_spare_part_price_update_view_renders(client, user_setup, mocker):
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.first(), price=50.00, effectivedate='2023-10-01'    )
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    price = Tblpartsprice.objects.last()
    url = reverse('parts:part_prices_update', kwargs={'pk': price.priceid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/part_prices_update.html')

@pytest.mark.django_db
def test_spare_part_price_update_view_post_successful(client, user_setup, mocker):
    Tblpartsprice.objects.create(partid=Tblpartslist.objects.last(), price=100.00, effectivedate='2023-10-01'    )
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    price = Tblpartsprice.objects.last()
    url = reverse('parts:part_prices_update', kwargs={'pk': price.priceid})
    data = {
        'partid': price.partid.partid,
        'price': 75.00,
        'effectivedate': '2023-11-01',
    }
    response = client.post(url, data)
    
    assert response.status_code == 302

    price.refresh_from_db()
    assert price.price == 75.00


#test PartLinkedModelListView
@pytest.mark.django_db
def test_part_linked_model_list_view_requires_login(client):
    url = reverse('parts:linked_models')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_part_linked_model_list_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:linked_models')
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_part_linked_model_list_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:linked_models')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/linked_models.html')

    #test with partid
    query_params = urlencode({'partid': 0})
    response_with_params = client.get(f"{url}?{query_params}")
    assert response_with_params.status_code == 200

#test LinkModelCreateTableView
@pytest.mark.django_db
def test_link_model_create_view_login_required(client):
    url = reverse('parts:linked_models_create')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_link_model_create_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:linked_models_create')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_link_model_create_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:linked_models_create')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/linked_model_create.html")

@pytest.mark.django_db
def test_link_model_create_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('parts:linked_models_create')
    
    part = Tblpartslist.objects.first()
    TblPartModel.objects.filter(part=part).delete()
    models = Tblmodel.objects.all()[:5]
    models_str = [model.pk for model in models]
    data = {
        'partid': part.partid,
        'models': models_str
    }
    response = client.post(url, data)
    
    assert response.status_code == 302

    new_link = TblPartModel.objects.last()
    assert new_link.part.partid == part.partid
    assert new_link.model.modelid == models_str[-1]

#test PartModelDeleteview

@pytest.mark.django_db
def test_link_model_delete_view_login_required(client):
    url = reverse('parts:linked_models_delete', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_link_model_delete_view_authentication_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('parts:linked_models_delete', kwargs={'pk': 0})
    response = client.get(url)
    assert response.status_code == 403  

@pytest.mark.django_db
def test_link_model_delete_view_renders(client, user_setup, mocker):

    TblPartModel.objects.create(part=Tblpartslist.objects.first(), model=Tblmodel.objects.first())
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    part_model = TblPartModel.objects.last()
    url = reverse('parts:linked_models_delete', kwargs={'pk': part_model.part_model_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'parts/partials/linked_model_delete.html')

@pytest.mark.django_db
def test_link_model_delete_view_post_htmx_successful(client, user_setup, mocker):
    TblPartModel.objects.create(part=Tblpartslist.objects.first(), model=Tblmodel.objects.first())
    TblPartModel.objects.create(part=Tblpartslist.objects.first(), model=Tblmodel.objects.last())

    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    part_model = TblPartModel.objects.last()
    url = reverse('parts:linked_models_delete', kwargs={'pk': part_model.part_model_id})
    response = client.post(url, HTTP_HX_REQUEST='true')
    
    assert response.status_code == 200

    with pytest.raises(TblPartModel.
                       DoesNotExist):
        part_model.refresh_from_db()

@pytest.mark.django_db
def test_link_model_delete_view_post_successful(client, user_setup, mocker):

    TblPartModel.objects.create(part=Tblpartslist.objects.first(), model=Tblmodel.objects.first())
    TblPartModel.objects.create(part=Tblpartslist.objects.first(), model=Tblmodel.objects.last())

    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    part_model = TblPartModel.objects.last()
    url = reverse('parts:linked_models_delete', kwargs={'pk': part_model.part_model_id})
    response = client.post(url)
    
    assert response.status_code == 302

    with pytest.raises(TblPartModel.
                       DoesNotExist):
        part_model.refresh_from_db()




