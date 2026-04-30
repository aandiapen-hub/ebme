from urllib.parse import urlencode
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from documents.models import TemporaryUpload
from documents.utils import clear_extraction_results, save_extraction_results
from procurement.models import TblSuppliers,TblPurchaseOrder, TblPoLines, TblDeliveries, TblDeliveryLines,TblInvoices
from django.core.files.uploadedfile import SimpleUploadedFile

from parts.models import Tblpartslist

from django.core.files import File
from django.contrib.messages import get_messages


#test PoTableView
@pytest.mark.django_db
def test_asset_create_view_requires_login(client):
    url = reverse('procurement:po')
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_po_table_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:po')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_po_table_view_renders(client, user_setup, mocker):

    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:po')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/purchaseorders.html')

    query_params = urlencode({'universal_search': 'test'})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

    #test htmx response
    response_htmx = client.get(url, HTTP_HX_REQUEST='true')
    assert response_htmx.status_code == 200

#test POCreateView
@pytest.mark.django_db
def test_po_create_view_requires_login(client): 
    url = reverse('procurement:po_create')
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page  

@pytest.mark.django_db
def test_po_create_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:po_create')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_po_create_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:po_create')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/po_create.html')

@pytest.mark.django_db
def test_po_create_view_post(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:po_create')
    
    data = {
        'supplier': 10001,  # Assuming supplier with ID 1 exists
        'date_raised': '2023-10-01',
    }
    
    response = client.post(url, data)
    assert response.status_code == 302

# test PoUpdateView
@pytest.mark.django_db
def test_po_update_view_requires_login(client):
    url = reverse('procurement:po_update', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_po_update_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:po_update', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_po_update_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:po_update', kwargs={'pk': po.po_id}) 
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/po_update.html')

@pytest.mark.django_db
def test_po_update_view_post(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:po_update', kwargs={'pk': po.po_id}) 
    supplier = TblSuppliers.objects.last()
    item = Tblpartslist.objects.filter(supplier_id=supplier.supplier_id).last()  # Assuming you have at least one part in the database
    
    data = {
        'supplier': str(supplier.supplier_id),  
        'date_raised': '2024-10-01',
        
        'tblpolines_set-TOTAL_FORMS': '1',
        'tblpolines_set-INITIAL_FORMS': '0',
        'tblpolines_set-MIN_NUM_FORMS': '0',
        'tblpolines_set-MAX_NUM_FORMS': '1000',

        # One form in the formset
        'tblpolines_set-0-item': str(item.partid),       
        'tblpolines_set-0-unit_price': '100.00',
        'tblpolines_set-0-qty_ordered': '2',

    }
    
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse('procurement:po_detail', kwargs={'pk': po.po_id})

@pytest.mark.django_db
def test_po_update_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:po_update', kwargs={'pk': po.po_id}) 
    supplier = TblSuppliers.objects.last()
    item = Tblpartslist.objects.filter(supplier_id=supplier.supplier_id).last()  # Assuming you have at least one part in the database
    
    data = {
        'supplier': str(supplier.supplier_id),  
        'date_raised': '',
        
        'tblpolines_set-TOTAL_FORMS': '1',
        'tblpolines_set-INITIAL_FORMS': '0',
        'tblpolines_set-MIN_NUM_FORMS': '0',
        'tblpolines_set-MAX_NUM_FORMS': '1000',

        # One form in the formset
        'tblpolines_set-0-item': str(item.partid),       
        'tblpolines_set-0-unit_price': '100.00',
        'tblpolines_set-0-qty_ordered': '',

    }
    
    response = client.post(url, data)
    assert response.status_code == 200


# test PoDeleteView
@pytest.mark.django_db
def test_po_delete_view_requires_login(client):
    url = reverse('procurement:po_delete', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_po_delete_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:po_delete', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_po_delete_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:po_delete', kwargs={'pk': po.po_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/po_delete.html')

@pytest.mark.django_db
def test_po_delete_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    TblDeliveries.objects.filter(po=po).delete()  # Ensure no deliveries are linked to the PO before deletion
    url = reverse('procurement:po_delete', kwargs={'pk': po.po_id}) 
    
    response = client.post(url)


    assert response.status_code == 200
    assert response['HX-Redirect'] == reverse('procurement:po')
    assert not TblPurchaseOrder.objects.filter(po_id=po.po_id).exists()  # Ensure the PO is deleted

@pytest.mark.django_db
def test_po_delete_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    TblPoLines.objects.create(
        po_id=po.po_id,
        item=Tblpartslist.objects.first(),  # Assuming you have at least one part in the database
        unit_price=100.00,
        qty_ordered=2
    )
    url = reverse('procurement:po_delete', kwargs={'pk': po.po_id}) 
    
    response = client.post(url)
    assert response.status_code == 200
    assert 'Error Details' in response.content.decode()  # Ensure error message is present


# test PoLinesListView
@pytest.mark.django_db
def test_po_lines_list_view_requires_login(client):
    url = reverse('procurement:po_lines')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db 
def test_po_lines_list_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:po_lines')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_po_lines_list_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:po_lines')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/partials/polines.html')

    #test with po specified in get
    query_params = urlencode({'po': 1})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

# test generate_purchase_order
@pytest.mark.django_db
def test_generate_purchase_order_requires_login(client):
    url = reverse('procurement:gen_po', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_generate_purchase_order_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:gen_po', kwargs={'pk': 1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_generate_purchase_order_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    TblPoLines.objects.create(
        po=po,
        item=Tblpartslist.objects.first(),  # Assuming you have at least one part in the database
        unit_price=100.00,
        qty_ordered=2,
        vat=0.2,
        line_description='Test Item',
        line_price=120.00  # Assuming line price is unit price + VAT
        
    )


    url = reverse('procurement:gen_po', kwargs={'pk': po.po_id})
    response = client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'


#test DeliveriesListView
@pytest.mark.django_db
def test_deliveries_list_view_requires_login(client):
    url = reverse('procurement:deliveries')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_deliveries_list_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:deliveries')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_deliveries_list_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:deliveries')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/partials/deliveries.html')

    #test with po specified in get
    query_params = urlencode({'po': 1})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

    query_params = urlencode({'delivery_id': 1})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

'# test DeliveryLinesListView'
@pytest.mark.django_db
def test_delivery_lines_list_view_requires_login(client):
    url = reverse('procurement:del_lines')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_delivery_lines_list_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:del_lines')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_delivery_lines_list_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:del_lines')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/partials/delivery_lines.html')

    #test with delivery specified in get
    query_params = urlencode({'delivery': 1})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

# test OustandingOrdersListView
@pytest.mark.django_db
def test_outstanding_orders_list_view_requires_login(client):
    url = reverse('procurement:outstanding_items')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_outstanding_orders_list_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:outstanding_items')
    response = client.get(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_outstanding_orders_list_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:outstanding_items')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/partials/outstanding_items.html')

    #test with po specified in get
    query_params = urlencode({'po': 1})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params)
    assert response_with_params.status_code == 200

# test DeliveryCreateView
@pytest.mark.django_db
def test_delivery_create_view_requires_login(client):
    url = reverse('procurement:deliveries_create')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_delivery_create_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:deliveries_create')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_delivery_create_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:deliveries_create')
    po = TblPurchaseOrder.objects.last()

    #test po_id in query params
    query_params = urlencode({'po_id': po.po_id})
    url_with_params = f"{url}?{query_params}"
    response = client.get(url_with_params)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/po_delivery.html')

    #test delivery_note_number in query params
    query_params = urlencode({'delivery_note_number': 1})
    url_with_params = f"{url}?{query_params}"
    response = client.get(url_with_params)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/po_delivery.html')

    #test items in query params
    item = TblPoLines.objects.create(
        po_id=po.po_id,
        item=Tblpartslist.objects.first(),  # Assuming you have at least one part in the database
        unit_price=100.00,
        qty_ordered=2,)
    from procurement.models import Outstandngdeliveriesview
    query_params = urlencode({'items': "{'1': '2', '2': '3'}", 'po_id': po.po_id})
    url_with_params = f"{url}?{query_params}"
    response = client.get(url_with_params)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/po_delivery.html')

@pytest.mark.django_db
def test_delivery_create_view_post_successfully(client, user_setup, mocker):

    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:deliveries_create')
    query_params = urlencode({'po_id': po.po_id})
    url_with_params = f"{url}?{query_params}"
    data = {
        'po': po,
        'delivery_date': '2023-10-01',
        'delivery_note_number': 'Test Delivery Notexx',
    
        # Management form data
        'tbldeliverylines_set-TOTAL_FORMS': '2',
        'tbldeliverylines_set-INITIAL_FORMS': '0',

        # Formset form 0
        'tbldeliverylines_set-0-product': '1',
        'tbldeliverylines_set-0-quantity': '10',

        # Formset form 1
        'tbldeliverylines_set-1-product': '2',
        'tbldeliverylines_set-1-quantity': '5',

    }
            
    response = client.post(url_with_params, data)

    created_delivery = TblDeliveries.objects.last() 
    assert response.status_code == 302
    assert response.url == reverse('procurement:po_detail', kwargs={'pk': created_delivery.po_id})

@pytest.mark.django_db
def test_delivery_create_view_post_successfully_with_document(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    user = user_setup
    client.force_login(user)
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:deliveries_create')
    query_params = urlencode({'po_id': po.po_id})
    url_with_params = f"{url}?{query_params}"

    import os
    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, 'test_files','delivery_note.jpeg')

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name="delivery_note.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpeg'
        )


    data = {
        'po': po,
        'delivery_date': '2023-10-01',
        'delivery_note_number': 'Test Delivery Notexx',
        'temp_file_group' : image.group,
    
        # Management form data
        'tbldeliverylines_set-TOTAL_FORMS': '2',
        'tbldeliverylines_set-INITIAL_FORMS': '0',

        # Formset form 0
        'tbldeliverylines_set-0-product': '1',
        'tbldeliverylines_set-0-quantity': '10',

        # Formset form 1
        'tbldeliverylines_set-1-product': '2',
        'tbldeliverylines_set-1-quantity': '5',

    }


            
    response = client.post(url_with_params, data)

    created_delivery = TblDeliveries.objects.last() 
    assert response.status_code == 302
    assert response.url == reverse('procurement:po_detail', kwargs={'pk': created_delivery.po_id})

@pytest.mark.django_db
def test_delivery_create_view_post_unsuccessfully(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    po = TblPurchaseOrder.objects.last()
    url = reverse('procurement:deliveries_create')
    query_params = urlencode({'po_id': po.po_id})
    url_with_params = f"{url}?{query_params}"
    data = {
    
        # Management form data
        'tbldeliverylines_set-TOTAL_FORMS': '2',
        'tbldeliverylines_set-INITIAL_FORMS': '0',

        # Formset form 0
        'tbldeliverylines_set-0-product': '1',
        'tbldeliverylines_set-0-quantity': '-5',

        # Formset form 1
        'tbldeliverylines_set-1-product': '2',
        'tbldeliverylines_set-1-quantity': '5',

    }
            
    response = client.post(url_with_params, data)

    created_delivery = TblDeliveries.objects.last() 
    assert response.status_code == 200 

#test DeliveryUpdateView
@pytest.mark.django_db
def test_delivery_update_view_requires_login(client):
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_update', kwargs={'pk': delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_delivery_update_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_update', kwargs={'pk': delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_delivery_update_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_update', kwargs={'pk': delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/delivery_update.html')    

@pytest.mark.django_db
def test_delivery_update_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()

    url = reverse('procurement:deliveries_update', kwargs={'pk': delivery.delivery_id})
    
    data = {
        #'po': delivery.po.po_id, #no po_id makes form invalid
        'delivery_date': '2023-10-01',
        'delivery_note_number': 'Updated Delivery Note',
        
        'tbldeliverylines_set-TOTAL_FORMS': '1',
        'tbldeliverylines_set-INITIAL_FORMS': '0',
        'tbldeliverylines_set-MIN_NUM_FORMS': '0',
        'tbldeliverylines_set-MAX_NUM_FORMS': '1000',

        # One form in the formset
        'tbldeliverylines_set-0-item': str(Tblpartslist.objects.last().partid),  # Assuming you have at least one part in the database
        'tbldeliverylines_set-0-qty_delivered': '2',
    }
    
    response = client.post(url, data)
    assert response.status_code == 200

@pytest.mark.django_db
def test_delivery_update_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    po = delivery.po
    supplier = po.supplier
    item = Tblpartslist.objects.filter(supplier_id=supplier).last()  # Assuming you have at least one part in the database
    url = reverse('procurement:deliveries_update', kwargs={'pk': delivery.delivery_id})
    
    data = {
        'po': delivery.po.po_id,
        'delivery_date': '2023-10-01',
        'delivery_note_number': 'Updated Delivery Note',
        
        'tbldeliverylines_set-TOTAL_FORMS': '1',
        'tbldeliverylines_set-INITIAL_FORMS': '0',
        'tbldeliverylines_set-MIN_NUM_FORMS': '0',
        'tbldeliverylines_set-MAX_NUM_FORMS': '1000',

        # One form in the formset

    }
    
    
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse('procurement:po_detail', kwargs={'pk': delivery.po})

@pytest.mark.django_db
def test_delivery_delete_view_requires_login(client):
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_delete', kwargs={'pk': delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_delivery_delete_view_required_permission(client, user_setup):
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_delete', kwargs={'pk': delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_delivery_delete_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_delete', kwargs={'pk': delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/partials/delivery_delete_view.html')

@pytest.mark.django_db
def test_delivery_delete_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_delete', kwargs={'pk': delivery.delivery_id})
    TblDeliveryLines.objects.filter(delivery=delivery).delete()  # Ensure no delivery lines are linked to the delivery before deletion
    response = client.post(url)
    assert response.status_code == 302
    TblDeliveries.objects.filter(delivery_id=delivery.delivery_id).exists() # Ensure the delivery is deleted

@pytest.mark.django_db
def test_delivery_delete_view_post_successful_htmx(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_delete', kwargs={'pk': delivery.delivery_id})
    TblDeliveryLines.objects.filter(delivery=delivery).delete()  # Ensure no delivery lines are linked to the delivery before deletion
    response = client.post(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert not TblDeliveries.objects.filter(delivery_id=delivery.delivery_id).exists() # Ensure the delivery is deleted


@pytest.mark.django_db
def test_delivery_delete_view_post_unsuccessful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    delivery = TblDeliveries.objects.last()
    url = reverse('procurement:deliveries_delete', kwargs={'pk': delivery.delivery_id})
    response = client.post(url)
    assert response.status_code == 200
    assert TblDeliveries.objects.filter(delivery_id=delivery.delivery_id).exists()  # Ensure the delivery is not deleted


@pytest.mark.django_db
def test_invoice_table_view_requires_login(client):
    url = reverse('procurement:invoices_table')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_invoice_table_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:invoices_table')
    response = client.get(url)
    assert response.status_code == 403



@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])

@pytest.mark.django_db
def test_invoice_table_view_renders(client, user_setup, mocker, search_term):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:invoices_table')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/invoices_table.html')

    #test htmx
    query_params = urlencode({'universal_search': search_term})
    url_with_params = f"{url}?{query_params}"
    response_with_params = client.get(url_with_params, HTTP_HX_REQUEST='true')
    assert response_with_params.status_code == 200

@pytest.mark.django_db
def test_invoice_create_view_requires_login(client):
    url = reverse('procurement:invoices_create')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_invoice_create_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:invoices_create')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoice_create_view_renders_with_ai_data(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:invoices_create')

    save_extraction_results(
        user_id=user,
        group=1,
        results={'invoice_no'  : '1234'
                },
        hours=1,
    )
    
    query_params = urlencode({'temp_file_group': '1'})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/invoices_create.html')

@pytest.mark.django_db
def test_invoice_create_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:invoices_create')
    clear_extraction_results(user, group=None)
    query_params = urlencode({'invoice_no': '1234'})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/invoices_create.html')

@pytest.mark.django_db
def test_invoice_create_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:invoices_create')
    po = TblPurchaseOrder.objects.last()
    TblPoLines.objects.create(
        po_id=po.po_id,
        item=Tblpartslist.objects.first(),  # Assuming you have at least one part in the database
        unit_price=100.00,
        qty_ordered=2,
    )
    
    data = { # Assuming supplier with ID 1 exists
        'invoice_no': 'INV-12345',
        'invoice_date': '2023-10-01',
        'po': po.po_id, 
        'invoice_status': 1,
        'invoice_amount': 10.00,
    }
    
    response = client.post(url, data)
    assert response.status_code == 302
    assert TblInvoices.objects.filter(invoice_no='INV-12345').exists()  # Ensure the invoice is created


@pytest.mark.django_db
def test_invoice_create_view_post_successful_with_document(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:invoices_create')
    po = TblPurchaseOrder.objects.first()

    import os
    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, 'test_files','delivery_note.jpeg')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpeg'
        )


    TblPoLines.objects.create(
        po_id=po.po_id,
        item=Tblpartslist.objects.first(),  # Assuming you have at least one part in the database
        unit_price=100.00,
        qty_ordered=2,
    )
    po.refresh_from_db()
    data = { # Assuming supplier with ID 1 exists
        'invoice_no': 'INV-12345',
        'invoice_date': '2023-10-01',
        'po': po.po_id, 
        'invoice_status': 1,
        'invoice_amount': 1.00,
        'temp_file_group' : image.group,
    }
        
    response = client.post(url, data)
    assert response.status_code == 302
    assert TblInvoices.objects.filter(invoice_no='INV-12345').exists()  # Ensure the invoice is created

@pytest.mark.django_db
def test_invoice_detail_view_requires_login(client):
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_detail', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_invoice_detail_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_detail', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoice_detail_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_detail', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/invoices_detail.html')    

@pytest.mark.django_db
def test_invoices_update_view_requires_login(client):
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_update', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_invoices_update_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_update', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoices_update_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_update', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/invoices_create.html')

@pytest.mark.django_db
def test_invoices_update_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_update', kwargs={'pk': invoice.invoice_id})
    
    data = {
        'invoice_no': 'INV-12345',
        'invoice_date': '2023-10-01',
        'po': invoice.po.po_id, 
        'invoice_status': 1,
        'invoice_amount': 10.00,
    }
    
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse('procurement:invoices_detail', kwargs={'pk': invoice.invoice_id})
    updated_invoice = TblInvoices.objects.get(invoice_id=invoice.invoice_id)
    assert updated_invoice.invoice_no == 'INV-12345'

@pytest.mark.django_db
def test_invoices_delete_view_requires_login(client):
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_delete', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_invoices_delete_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_delete', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoices_delete_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_delete', kwargs={'pk': invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/invoices_delete.html')

@pytest.mark.django_db
def test_invoices_delete_view_post_successful(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    invoice = TblInvoices.objects.last()
    url = reverse('procurement:invoices_delete', kwargs={'pk': invoice.invoice_id})
    
    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('procurement:invoices_table')
    assert not TblInvoices.objects.filter(invoice_id=invoice.invoice_id).exists()   

@pytest.mark.django_db
def test_invoice_list_view_requires_login(client):
    url = reverse('procurement:invoiceslist')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_invoice_list_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse('procurement:invoiceslist')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoice_list_view_renders(client, user_setup, mocker):
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user_setup)
    url = reverse('procurement:invoiceslist')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'procurement/partials/invoices_list.html')

    #test with query params
    po = TblPurchaseOrder.objects.last()
    query_params = urlencode({'po': po.po_id})
    full_url = f"{url}?{query_params}"
    response_with_params = client.get(full_url)
    assert response_with_params.status_code == 200
    assertTemplateUsed(response_with_params, 'procurement/partials/invoices_list.html')


#test delivery note reader

@pytest.mark.django_db
def test_delivery_note_reader_requires_login(client):
    url = reverse('procurement:delivery_note_reader', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_delivery_note_reader_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:delivery_note_reader', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_delivery_note_reader_post(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_files','delivery_note.jpeg')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpeg'
        )
    group = image.group
    
        
    url = reverse('procurement:delivery_note_reader', kwargs={'temp_file_group':group})
    response = client.post(url)
    assert response.status_code == 200
    assert 'reader_output' in response['HX-Redirect']

"""
@pytest.mark.django_db
def test_delivery_note_reader_post_incorrect_file(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_files','invoice1.pdf')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="invoice1.pdf") 
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'application/pdf'
        )
    group = image.group
        
    url = reverse('procurement:delivery_note_reader', kwargs={'temp_file_group':group})
    response = client.post(url)
    error_messages = list(get_messages(response.wsgi_request))
    assert any(
            "No Delivery Information" in str(message) for message in error_messages
    )
"""


#test delivery note reader output
@pytest.mark.django_db
def test_delivery_note_reader_output_requires_login(client):
    url = reverse('procurement:delivery_note_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_delivery_note_reader_output_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:delivery_note_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_delivery_note_reader_output_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    po = TblPurchaseOrder.objects.last()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'po':po.po_id,
                 'DelNote':'12345'
                },
        hours=1,
    )


    url = reverse('procurement:delivery_note_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'procurement/partials/delivery_note_reader_output.html')

@pytest.mark.django_db
def test_delivery_note_reader_output_view_renders_no_delivery_info(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    po = TblPurchaseOrder.objects.last()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={},
        hours=1,
    )


    url = reverse('procurement:delivery_note_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert 'No delivery note data' in response.context['error']

@pytest.mark.django_db
def test_delivery_note_reader_output_view_renders_existing_delivery(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user)
    delivery_note = TblDeliveries.objects.first()

    save_extraction_results(
        user_id=user,
        group=1,
        results={'PO':delivery_note.po_id,
                 'DelNote':delivery_note.delivery_note_number,
                },
        hours=1,
    )

    url = reverse('procurement:delivery_note_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.context['existing_delivery']

@pytest.mark.django_db
def test_delivery_note_reader_output_view_renders_unknown_po(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'po':'12',
                 'DelNote':'12345'
                },
        hours=1,
    )


    url = reverse('procurement:delivery_note_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assert "Purchase order not recognised" in response.context['error'] 



#test invoice reader

@pytest.mark.django_db
def test_invoice_reader_requires_login(client):
    url = reverse('procurement:invoices_reader', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_invoice_reader_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:invoices_reader', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoice_reader_post(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_files','invoice1.pdf')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="invoice1.pdf")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'application/pdf'
        )
    group = image.group
        
    url = reverse('procurement:invoices_reader', kwargs={'temp_file_group':group})
    response = client.post(url)
    assert response.status_code == 200
    assert 'reader_output' in response['HX-Redirect']

"""@pytest.mark.django_db
def test_invoice_reader_post_incorrect_file(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, 'test_files','delivery_note.jpeg')

    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, 
            file= testFile,
            file_size = testFile.size,
            mime_type = 'image/jpeg'
        )
    group = image.group
        
    url = reverse('procurement:invoices_reader', kwargs={'temp_file_group':group})
    response = client.post(url)
    assert response.status_code == 200
    error_messages = list(get_messages(response.wsgi_request))
    assert any(
            "No Invoice Information" in str(message) for message in error_messages
    )
"""

#test invoice reader output

@pytest.mark.django_db
def test_invoice_reader_output_requires_login(client):
    url = reverse('procurement:invoices_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_invoice_reader_output_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse('procurement:invoices_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_invoices_reader_output_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    po = TblPurchaseOrder.objects.last()
    invoice = TblInvoices.objects.last()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'po':po.po_id,
                 'invoice_no'  : invoice.invoice_no,
                },
        hours=1,
    )

    url = reverse('procurement:invoices_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'procurement/partials/invoice_reader_output.html')

@pytest.mark.django_db
def test_invoices_reader_output_view_renders_new_invoice(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    po = TblPurchaseOrder.objects.last()
    invoice = TblInvoices.objects.last()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'po':po.po_id,
                 'invoice_no'  : '1234'
                },
        hours=1,
    )

    url = reverse('procurement:invoices_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response,'procurement/partials/invoice_reader_output.html')


@pytest.mark.django_db
def test_invoices_reader_output_view_renders_no_invoice_data(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    po = TblPurchaseOrder.objects.last()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={ },
        hours=1,
    )

    url = reverse('procurement:invoices_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assert 'No invoice data' in response.context['error']


@pytest.mark.django_db
def test_invoices_reader_output_view_renders_uknown_po(client, user_setup, mocker):
    user = user_setup
    mocker.patch('django.contrib.auth.mixins.PermissionRequiredMixin.has_permission', return_value=True)
    po = TblPurchaseOrder.objects.last()
    client.force_login(user)

    save_extraction_results(
        user_id=user,
        group=1,
        results={'po':'1234' },
        hours=1,
    )

    url = reverse('procurement:invoices_reader_output', kwargs={'temp_file_group':1})
    response = client.get(url)
    assert response.status_code == 200
    assert 'order not recognised' in response.context['error']