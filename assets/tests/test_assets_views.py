from asyncio import QueueEmpty
from tokenize import group
from typing import assert_never
from unicodedata import category
import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from assets.models import (Tblassets, Tblmodel,
                            Tblcustomer, Tblbrands,
                            Tblcategories,TblAssetStatus,
                            Tblppmschedules,Tbljob)
from assets.views import AssetJobsListView
from django.test import RequestFactory
from unittest.mock import patch

from documents.models import TemporaryUpload
from documents.utils import get_extraction_results, save_extraction_results
from .factories import AssetFactory
from urllib.parse import urlencode
from django.core.files import File

from django.contrib.messages import get_messages



#test AssetCreateView
@pytest.mark.django_db
def test_asset_create_view_requires_login(client):
    url = reverse('assets:create_asset')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_create_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse('assets:create_asset')
    response = client.get(url)
    
    assert response.status_code == 403  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.django_db
def test_asset_create_view_success_post(client, user_setup,mocker):
    # Create user and force login
    user = user_setup
    
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    client.force_login(user)

    # Set up required related objects
    category_instance = Tblcategories.objects.create(categoryname='medical device')
    brand_instance = Tblbrands.objects.create(brandname='ashwin_coop')
    model_instance = Tblmodel.objects.create(modelname='TestModel', brandid=brand_instance, categoryid=category_instance)
    customer_instance = Tblcustomer.objects.last()
    asset_status_instance = TblAssetStatus.objects.first()
    ppm_schedule_instance = Tblppmschedules.objects.create(scheduleid=10, schedulefrequency=2)

    # Prepare form data
    form_data = {
        'modelid': model_instance.modelid,
        'customerid': customer_instance.customerid,
        'serialnumber': 12332,
        'asset_status_id': asset_status_instance.asset_status_id,
        'ppmscheduleid': ppm_schedule_instance.scheduleid,
    }
    url = reverse('assets:create_asset')
    response = client.post(url, data=form_data)
    created_asset = Tblassets.objects.last()
    assert created_asset.serialnumber == '12332'
    created_asset = Tblassets.objects.last()


# test AssetUpdateView
@pytest.mark.django_db
def test_asset_update_view_requires_login(client):
    asset = Tblassets.objects.last()
    url = reverse('assets:update_asset',kwargs={'pk': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_update_view_permission_denied(client,user_setup):
    asset = Tblassets.objects.last()
    user = user_setup
    client.force_login(user)

    #test denied permission
    url = reverse('assets:update_asset',kwargs={'pk': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 403  



@pytest.mark.django_db
def test_asset_update_view_renders(client,user_setup,mocker):
    asset = Tblassets.objects.last()
    user = user_setup
    client.force_login(user)

    user.customerid = asset.customerid
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)


    url = reverse('assets:update_asset',kwargs={'pk': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'assets/update_form.html')


@pytest.mark.django_db
def test_asset_update_view_valid_data_updates_object(client,user_setup,mocker):
    asset = Tblassets.objects.last()
    user = user_setup

    
    client.force_login(user)

    user.customerid = asset.customerid
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    url = reverse('assets:update_asset',kwargs={'pk': asset.assetid}) 
    response = client.post(url, data={
        'serialnumber': 'updated_serialnumber',
        'customerid': asset.customerid.customerid,  # Include the primary key of the customer
        'modelid': asset.modelid.modelid,
    })
    
    asset.refresh_from_db()
    assert asset.serialnumber == 'updated_serialnumber'
    assert response.status_code == 302  # Redirect after success

@pytest.mark.django_db
def test_asset_delete_view_login(client):
    asset = Tblassets.objects.last()

    url = reverse('assets:delete_asset',kwargs={'pk': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page
    
@pytest.mark.django_db
def test_asset_delete_view_permission_denied(client,user_setup):
    asset = Tblassets.objects.last()
    user = user_setup
    client.force_login(user)
    url = reverse('assets:delete_asset',kwargs={'pk': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 403  

@pytest.mark.django_db
def test_asset_delete_view_renders(client,user_setup,mocker):
    asset = Tblassets.objects.last()
    user = user_setup
    
    user.customerid = asset.customerid
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)


    client.force_login(user)
    url = reverse('assets:delete_asset',kwargs={'pk': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'assets/partials/delete_modal.html')
    assert response.context["view_type"] == 'delete' 

@pytest.mark.django_db
def test_asset_delete_view_post_success(client,user_setup,mocker):
    asset = AssetFactory()
    
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    user.customerid = asset.customerid
    user.save()

    client.force_login(user)
    url = reverse('assets:delete_asset',kwargs={'pk': asset.assetid}) 
    response = client.post(url)


    assert 'HX-Redirect' in response
    assert response['HX-Redirect'] == reverse('assets:assets_list')

@pytest.mark.django_db
def test_asset_delete_view_handles_exception(client,user_setup,mocker):
    asset = Tblassets.objects.last()
    user = user_setup
    
    user.customerid = asset.customerid
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)


    client.force_login(user)
    # Mock the delete method to raise an exception
    with patch('assets.models.Tblassets.delete', side_effect=Exception("Mocked deletion error")):
        url = reverse('assets:delete_asset', kwargs={'pk': asset.assetid})
        response = client.post(url)

        # Assert the response status code
        assert response.status_code == 200  # The view renders the template with the error message

        from django.contrib.messages import get_messages    
        storage = list(get_messages(response.wsgi_request))
        assert any("An error occurred" in str(msg) for msg in storage)
        # Assert the template used
        assertTemplateUsed(response, 'assets/partials/delete_modal.html')

@pytest.mark.django_db
def test_filtered_asset_table_view_login(client,):
    url = reverse('assets:assets_list') 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_filtered_asset_table_view_permission_denied(client,user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('assets:assets_list') 
    response = client.get(url)
    assert response.status_code == 403  



@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])

@pytest.mark.django_db
def test_filtered_asset_table_view_renders(django_db_setup, client,user_setup,mocker,search_term):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    user.customerid = Tblassets.objects.first().customerid
    user.save()    
    client.force_login(user)

    url = reverse('assets:assets_list') 

    #test html get
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,"assets/assetview_filter.html")
    content = response.content.decode()

    
    #test htmx get
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200

    #test with query parameters
    query_params = urlencode({'universal_search' : search_term})
    url_with_params = f"{url}?{query_params}"
    response = client.get(url_with_params, HTTP_HX_REQUEST='true') 
    assert response.status_code == 200



@pytest.mark.django_db
def test_filtered_asset_filterset(django_db_setup, client,user_setup,mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    user.customerid = Tblassets.objects.first().customerid
    user.save()    
    client.force_login(user)

    base_url = reverse('assets:assets_list')

    #test supersearch 
    query_string = urlencode({'supersearch': 'Meditech 123 $ bla bla'})
    url =   f"{base_url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200

    
@pytest.mark.django_db
def test_Asset_job_list_view_login(client,):
    asset = Tblassets.objects.last()
    url = reverse('assets:asset_jobs', kwargs={'assetid': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_Asset_job_list_view_permission_denied(client,user_setup):
    user = user_setup
    client.force_login(user)
    asset = Tblassets.objects.last()
    url = reverse('assets:asset_jobs', kwargs={'assetid': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 403  


@pytest.mark.django_db
def test_Asset_job_list_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    asset = Tblassets.objects.first()
    jobs = Tbljob.objects.filter(assetid=asset.assetid)

    url = reverse('assets:asset_jobs', kwargs={'assetid': asset.assetid}) 
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,"assets/partials/job_summary.html")
    for job in jobs:
        assert str(job.jobid) in response.content.decode()


@pytest.mark.django_db
def test_get_queryset_returns_none_if_no_assetid():
    factory = RequestFactory()
    request = factory.get('/fake-url/')
    
    # Instantiate the view and assign request
    view = AssetJobsListView()
    view.request = request
    view.kwargs = {}  # assetid is missing

    qs = view.get_queryset()
    assert qs.count() == 0  # or assert list(qs) == []

@pytest.mark.django_db
def test_get_queryset_returns_none_if_assetid_not_found(client,user_setup,mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid

    user.save()
    client.force_login(user)

    factory = RequestFactory()
    request = factory.get('/fake-url/')
    request.user = user
    
    # Instantiate the view and assign request
    view = AssetJobsListView()
    view.request = request
    view.kwargs = {'assetid': 9999}  # assetid is missing

    qs = view.get_queryset()
    assert qs.count() == 0  # or assert list(qs) == []

@pytest.mark.django_db
def test_bar_code_reader_requires_login(client):
    url = reverse('assets:barcode_scanner', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_bar_code_reader_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('assets:barcode_scanner', kwargs={'temp_file_group':0})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_bar_code_reader_post(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_images', 'gs1_id_label.jpg')

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name="test_img1.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpg'
        )
    group = image.group
        
    url = reverse('assets:barcode_scanner', kwargs={'temp_file_group':group})
    response = client.post(url)
    assert response.status_code == 200
    assertTemplateUsed('assets/partials/barcode_scanner_output.html')

    extracted_data = get_extraction_results(user,group)
    assert '04052682013744' in extracted_data.values()
    assert 'gtin' in extracted_data.keys()


@pytest.mark.django_db
def test_bar_code_reader_post_with_ai(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_images', 'gs1_id_label.jpg')

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name="test_img1.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpg'
        )
    group = image.group
        
    url = reverse('assets:barcode_scanner', kwargs={'temp_file_group':0})
    query_params = urlencode({'use_ai':'true'})
    full_url = f"{url}?{query_params}"
    response = client.post(full_url)
    assert response.status_code == 200
    assertTemplateUsed('assets/partials/barcode_scanner_output.html')


@pytest.mark.django_db
def test_bar_code_reader_post_incorrect_document_type(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_images', 'delivery_note.jpeg')



    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name="test_img1.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpg'
        )
    group = image.group
    
        
    url = reverse('assets:barcode_scanner', kwargs={'temp_file_group':group})
    response = client.post(url)
    assert response.status_code == 200
    assertTemplateUsed("partials/messages.html")
    error_messages = list(get_messages(response.wsgi_request))
    assert any(
            "No barcodes recognised from these images" in str(message) for message in error_messages
        )

@pytest.mark.django_db
def test_bar_code_reader_post_incorrect_document_format(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_images', 'filter.svg')

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name="filter.svg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'svg'
        )
    group = image.group
        
    url = reverse('assets:barcode_scanner', kwargs={'temp_file_group':group})
    response = client.post(url)
    assert response.status_code == 200
    assertTemplateUsed("partials/messages.html")
    error_messages = list(get_messages(response.wsgi_request))
    assert any(
            "Incorrect file type" in str(message) for message in error_messages
        )
    
@pytest.mark.django_db
def test_barcode_output_view_requires_login(client):
    url = reverse('assets:barcode_output', kwargs={'temp_file_group':1})

    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_barcode_output_view_permission_required(client, user_setup):
    user = user_setup

    client.force_login(user)
    url = reverse('assets:barcode_output',kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_barcode_output_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'gtin': '040526820137445',
                'serialnumber': '25057712',
                'prod_date': '2021-10-21',
                'customerassetnumber': '',
                'suggested_brands': ['test brand'],
                'suggested_categories': ['test category']},
        hours=1,
    )
    


    url = reverse('assets:barcode_output', kwargs={'temp_file_group':1})

    response = client.get(url)
    assert response.status_code == 200
    
    assert response.context['form'].initial['gtin'] == '040526820137445'
    assertTemplateUsed(response, "assets/partials/barcode_scanner_output.html")

    #save gtin to model 1
    model = Tblmodel.objects.get(modelid=1)
    model.gtin = '040526820137445'
    model.save()
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_barcode_output_view_renders_with_no_gtin(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'serialnumber': '25057712', 'prod_date': '2021-10-21', 'customerassetnumber': '', 'modelname': '', 'suggested_brands': None, 'suggested_categories': None},
        hours=1,
    )


    url = reverse('assets:barcode_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['form'].initial['serialnumber'] == '25057712'
    assertTemplateUsed(response, "assets/partials/barcode_scanner_output.html")

@pytest.mark.django_db
def test_barcode_output_view_post_create_model(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    Tblmodel.objects.filter(gtin='04052682013744').delete()


    save_extraction_results(
        user_id=user,
        group=1,
        results={'gtin': '04052682013744', 'serialnumber': '25057712', 'prod_date': '2021-10-21', 'customerassetnumber': '', 'modelname': '', 'suggested_brands': None, 'suggested_categories': None},
        hours=1,
    )


    url = reverse('assets:barcode_output',kwargs={'temp_file_group':1})

    data = {
        'gtin': '04052682013744',
        'brandid': 1,
        'categoryid': 1,
        'modelname': 'Test Model',
        }

    response = client.post(url, data=data)
    assert Tblmodel.objects.filter(gtin='04052682013744').exists()
    assert response.status_code == 302


@pytest.mark.django_db
def test_barcode_output_view_post_create_asset(client, user_setup, mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    customerid = Tblassets.objects.first().customerid
    user.customerid = customerid
    user.save()
    client.force_login(user)
    

    import os
    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_images', 'gs1_id_label.jpg')
    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name="test_img1.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpg'
        )
 
    save_extraction_results(
        user_id=user,
        group=1,
        results={'gtin': '04052682013744', 'serialnumber': '25057712', 'prod_date': '2021-10-21', 'customerassetnumber': '', 'modelname': '', 'suggested_brands': None, 'suggested_categories': None},
        hours=1,
    )
    


    model = Tblmodel.objects.get(modelid=1)
    model.gtin = '04052682013744'
    model.save()

    data = {
        'serialnumber': '25057712',
        'modelid': 1,
        'customerid': customerid.pk,
        }


    url = reverse('assets:barcode_output',kwargs={'temp_file_group':1})

    response = client.post(url, data=data)

    assert response.status_code == 302
    assert Tblassets.objects.filter(serialnumber='25057712').exists()


# test asset barcode recognises existing asset
@pytest.mark.django_db
def test_barcode_output_view_redirects_to_existing_asset(client,user_setup,mocker):
    user = user_setup
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)
    asset = Tblassets.objects.last()
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'gtin': '04052682013744', 'serialnumber': asset.serialnumber, 'prod_date': '2021-10-21', 'customerassetnumber': '', 'modelname': '', 'suggested_brands': None, 'suggested_categories': None},
        hours=1,
    )

    url = reverse('assets:barcode_output', kwargs={'temp_file_group':1})
 
    #test htmx
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert response['HX-Redirect'] == reverse('assets:view_asset', kwargs={'pk': asset.assetid})

    #test normal request
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse('assets:view_asset', kwargs={'pk': asset.assetid})


#quick brand create view tests
@pytest.mark.django_db
def test_quick_brand_create_view_requires_login(client):
    url = reverse('assets:quick_create_brand')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_quick_brand_create_view_permission_required(client,user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('assets:quick_create_brand')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_quick_brand_create_view_posts(client,user_setup,mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',return_value=True)
    client.force_login(user)

    url = reverse('assets:quick_create_brand')
    data = {'brandname':'testbrand'}
    response = client.post(url,data)
    assert response.status_code == 200
    assert response['HX-Retarget'] == "#brands_list"
    assertTemplateUsed(response, "model_information/partials/brand_set_select.html")

#quick category create view tests
@pytest.mark.django_db
def test_quick_category_Create_view_requires_login(client):
    url = reverse('assets:quick_create_category')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()


@pytest.mark.django_db
def test_quick_category_create_view_permission_required(client,user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('assets:quick_create_category')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_quick_category_create_view_posts(client,user_setup,mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',return_value=True)
    client.force_login(user)

    url = reverse('assets:quick_create_category')
    data = {'categoryname':'testcategory'}
    response = client.post(url,data)
    assert response.status_code == 200
    assert response['HX-Retarget'] == "#categories_list"
    assertTemplateUsed(response, "model_information/partials/category_set_select.html")

#test quick model gtin update view
@pytest.mark.django_db
def test_quick_model_gtin_update_view_requires_login(client):
    url = reverse('assets:quick_update_model', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_quick_model_gtin_update_view_permission_required(client,user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('assets:quick_update_model', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_quick_model_gtin_update_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid

    user.save()
    client.force_login(user)

    base_url = reverse('assets:quick_update_model', kwargs={'pk': 1})
    query_params = urlencode({'temp_document_group':1})
    url = f"{base_url}?{query_params}"
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_quick_model_gtin_update_view_posts(client,user_setup,mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)

    model = Tblmodel.objects.get(modelid=1)
    model.gtin = ''
    model.save()

    url = reverse('assets:quick_update_model', kwargs={'pk': 1})
    data = {'gtin':'04052682013744','categoryid':1,'brandid':1,'modelname':'test model','temp_document_group':'1'}
    response = client.post(url,data)
    assert response.status_code == 302
    assert response.url == f"{reverse('assets:barcode_output', kwargs={'temp_file_group':1})}"
    model.refresh_from_db()
    assert model.gtin == '04052682013744'
