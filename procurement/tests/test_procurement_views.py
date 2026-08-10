from urllib.parse import urlencode
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed
from django.contrib.auth.models import Permission

from procurement.models import (
    TblSuppliers,
    TblPurchaseOrder,
    TblDeliveries,
    TblInvoices,
)


# test PoTableView
@pytest.mark.django_db
def test_po_table_view_requires_login(client):
    url = reverse("procurement:po")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_po_table_view_permission_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("procurement:po")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_po_table_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="view_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)

    url = reverse("procurement:po")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "filter_table.html")

    # test htmx response
    response_htmx = client.get(url, HTTP_HX_REQUEST="true")
    assert response_htmx.status_code == 200


# test POCreateView
@pytest.mark.django_db
def test_po_create_view_requires_login(client):
    url = reverse("procurement:po_create")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_po_create_view_permission_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("procurement:po_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_po_create_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="add_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("procurement:po_create")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/po_create.html")


@pytest.mark.django_db
def test_po_create_view_post(client, user, supplier):
    user = user()
    permission = Permission.objects.get(codename="add_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("procurement:po_create")

    data = {
        "supplier": supplier().pk,  # Assuming supplier with ID 1 exists
        "date_raised": "2023-10-01",
    }

    response = client.post(url, data)
    assert response.status_code == 302


# test PoUpdateView
@pytest.mark.django_db
def test_po_update_view_requires_login(client, purchase_order):
    po = purchase_order()
    url = reverse("procurement:po_update", kwargs={"pk": po.pk})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_po_update_view_permission_required(client, user, purchase_order):
    po = purchase_order()
    user = user()
    client.force_login(user)
    url = reverse("procurement:po_update", kwargs={"pk": po.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_po_update_view_renders(client, user, purchase_order):
    user = user()
    permission = Permission.objects.get(codename="change_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)

    po = purchase_order()
    url = reverse("procurement:po_update", kwargs={"pk": po.po_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/po_update.html")


@pytest.mark.django_db
def test_po_update_view_post(client, user, purchase_order, part):
    user = user()
    permission = Permission.objects.get(codename="change_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = purchase_order()
    url = reverse("procurement:po_update", kwargs={"pk": po.po_id})
    item = part()

    data = {
        "supplier": str(item.supplier_id.pk),
        "date_raised": "2024-10-01",
        "po_line-TOTAL_FORMS": "1",
        "po_line-INITIAL_FORMS": "0",
        "po_line-MIN_NUM_FORMS": "0",
        "po_line-MAX_NUM_FORMS": "1000",
        # One form in the formset
        "po_line-0-item": str(item.partid),
        "po_line-0-unit_price": "100.00",
        "po_line-0-qty_ordered": "2",
    }

    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("procurement:po_detail", kwargs={"pk": po.po_id})


@pytest.mark.django_db
def test_po_update_view_post_unsuccessful(client, user, purchase_order, part):
    user = user()
    permission = Permission.objects.get(codename="change_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = purchase_order()
    url = reverse("procurement:po_update", kwargs={"pk": po.po_id})
    supplier = TblSuppliers.objects.last()
    item = part()

    data = {
        "supplier": str(item.supplier_id.pk),
        "date_raised": "",
        "tblpolines_set-TOTAL_FORMS": "1",
        "tblpolines_set-INITIAL_FORMS": "0",
        "tblpolines_set-MIN_NUM_FORMS": "0",
        "tblpolines_set-MAX_NUM_FORMS": "1000",
        # One form in the formset
        "tblpolines_set-0-item": str(item.partid),
        "tblpolines_set-0-unit_price": "100.00",
        "tblpolines_set-0-qty_ordered": "",
    }

    response = client.post(url, data)
    assert response.status_code == 200


# test PoDeleteView
@pytest.mark.django_db
def test_po_delete_view_requires_login(client, purchase_order):
    po = purchase_order()
    url = reverse("procurement:po_delete", kwargs={"pk": po.pk})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_po_delete_view_permission_required(client, user, purchase_order):
    user = user()
    po = purchase_order()
    client.force_login(user)
    url = reverse("procurement:po_delete", kwargs={"pk": po.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_po_delete_view_renders(client, user, purchase_order):
    user = user()
    permission = Permission.objects.get(codename="delete_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = purchase_order()
    url = reverse("procurement:po_delete", kwargs={"pk": po.po_id})
    response = client.get(url)
    assertTemplateUsed(response, "procurement/po_delete.html")


@pytest.mark.django_db
def test_po_delete_view_post_successful(client, user, purchase_order):
    user = user()
    permission = Permission.objects.get(codename="delete_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = purchase_order()
    url = reverse("procurement:po_delete", kwargs={"pk": po.po_id})
    response = client.post(url)

    assert response.status_code == 302
    assert not TblPurchaseOrder.objects.filter(
        po_id=po.po_id
    ).exists()  # Ensure the PO is deleted


@pytest.mark.django_db
def test_po_delete_view_post_unsuccessful(client, user, po_line):
    user = user()
    po_line = po_line()
    permission = Permission.objects.get(codename="delete_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("procurement:po_delete", kwargs={"pk": po_line.po_id})

    response = client.post(url)
    assert response.status_code == 200
    assert response.context["form"].errors


# test generate_purchase_order
@pytest.mark.django_db
def test_generate_purchase_order_requires_login(client, purchase_order):
    po = purchase_order()
    url = reverse("procurement:gen_po", kwargs={"pk": po.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_generate_purchase_order_permission_required(client, user, po_line):
    po_line = po_line()
    user = user()
    client.force_login(user)
    url = reverse("procurement:gen_po", kwargs={"pk": po_line.po_id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_generate_purchase_order_renders(client, user, po_line):
    user = user()
    po_line = po_line()
    permission = Permission.objects.get(codename="view_tblpurchaseorder")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = po_line.po_id

    url = reverse("procurement:gen_po", kwargs={"pk": po})
    response = client.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


# test DeliveryCreateView
@pytest.mark.django_db
def test_delivery_create_view_requires_login(client, po_line):
    po_line = po_line()
    po = po_line.po_id

    url = reverse("procurement:deliveries_create", kwargs={"po_id": po})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_delivery_create_view_permission_required(client, user, po_line):
    user = user()
    client.force_login(user)
    po_line = po_line()
    po = po_line.po_id

    url = reverse("procurement:deliveries_create", kwargs={"po_id": po})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_delivery_create_view_renders(client, user, po_lines, purchase_order):
    user = user()
    permission = Permission.objects.get(codename="add_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = purchase_order()
    po_lines = po_lines(po=po)

    url = reverse("procurement:deliveries_create", kwargs={"po_id": po})
    # test po_id in query params
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/delivery_create.html")

    # test delivery_note_number in query params
    query_params = urlencode({"delivery_note_number": 1})
    url_with_params = f"{url}?{query_params}"
    response = client.get(url_with_params)
    assert response.status_code == 200


@pytest.mark.django_db
def test_delivery_create_view_post_successfully(client, user, part, po_line):
    user = user()
    po_line = po_line()
    po_line.save()

    permission = Permission.objects.get(codename="add_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    po = po_line.po_id
    url = reverse("procurement:deliveries_create", kwargs={"po_id": po})
    data = {
        "po": po,
        "delivery_date": "2023-10-01",
        "delivery_note_number": "Test Delivery Notexx",
        # Management form data
        "line-TOTAL_FORMS": "2",
        "line-INITIAL_FORMS": "0",
        # Formset form 0
        "line-0-product": part().pk,
        "line-0-quantity": "10",
        # Formset form 1
        "line-1-product": part().pk,
        "line-1-quantity": "5",
    }

    response = client.post(url, data)

    created_delivery = TblDeliveries.objects.last()
    assert response.status_code == 302
    assert response.url == reverse(
        "procurement:po_detail", kwargs={"pk": created_delivery.po_id}
    )


@pytest.mark.django_db
def test_delivery_create_view_post_unsuccessfully(client, user, po_line):
    user = user()
    permission = Permission.objects.get(codename="add_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    po_line = po_line()
    po = po_line.po_id
    url = reverse("procurement:deliveries_create", kwargs={"po_id": po})
    data = {
        # Management form data
        "tbldeliverylines_set-TOTAL_FORMS": "2",
        "tbldeliverylines_set-INITIAL_FORMS": "0",
        # Formset form 0
        "tbldeliverylines_set-0-product": "1",
        "tbldeliverylines_set-0-quantity": "-5",
        # Formset form 1
        "tbldeliverylines_set-1-product": "2",
        "tbldeliverylines_set-1-quantity": "5",
    }
    response = client.post(url, data)

    assert response.status_code == 200


# test DeliveryUpdateView
@pytest.mark.django_db
def test_delivery_update_view_requires_login(client, delivery):
    delivery = delivery()
    url = reverse("procurement:deliveries_update", kwargs={"pk": delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_delivery_update_view_permission_required(client, user, delivery):
    user = user()
    client.force_login(user)
    delivery = delivery()
    url = reverse("procurement:deliveries_update", kwargs={"pk": delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_delivery_update_view_renders(client, user, delivery):
    user = user()
    permission = Permission.objects.get(codename="change_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    delivery = delivery()
    url = reverse("procurement:deliveries_update", kwargs={"pk": delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/delivery_update.html")


@pytest.mark.django_db
def test_delivery_update_view_post_unsuccessful(client, user, delivery, part):
    user = user()
    permission = Permission.objects.get(codename="change_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    delivery = delivery()

    url = reverse("procurement:deliveries_update", kwargs={"pk": delivery.delivery_id})

    data = {
        #'po': delivery.po.po_id, #no po_id makes form invalid
        "delivery_date": "2023-10-01",
        "delivery_note_number": "Updated Delivery Note",
        "tbldeliverylines_set-TOTAL_FORMS": "1",
        "tbldeliverylines_set-INITIAL_FORMS": "0",
        "tbldeliverylines_set-MIN_NUM_FORMS": "0",
        "tbldeliverylines_set-MAX_NUM_FORMS": "1000",
        # One form in the formset
        "tbldeliverylines_set-0-item": str(
            part().pk
        ),  # Assuming you have at least one part in the database
        "tbldeliverylines_set-0-qty_delivered": "2",
    }

    response = client.post(url, data)
    assert response.status_code == 200


@pytest.mark.django_db
def test_delivery_update_view_post_successful(client, user, delivery):
    user = user()
    permission = Permission.objects.get(codename="change_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    delivery = delivery()
    url = reverse("procurement:deliveries_update", kwargs={"pk": delivery.delivery_id})

    data = {
        "po": delivery.po.po_id,
        "delivery_date": "2023-10-01",
        "delivery_note_number": "Updated Delivery Note",
        "line-TOTAL_FORMS": "1",
        "line-INITIAL_FORMS": "0",
        "line-MIN_NUM_FORMS": "0",
        "line-MAX_NUM_FORMS": "1000",
        # One form in the formset
    }

    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("procurement:po_detail", kwargs={"pk": delivery.po})


@pytest.mark.django_db
def test_delivery_delete_view_requires_login(client, delivery):
    delivery = delivery()
    url = reverse("procurement:deliveries_delete", kwargs={"pk": delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_delivery_delete_view_required_permission(client, user, delivery):
    user = user()
    delivery = delivery()
    client.force_login(user)
    delivery = TblDeliveries.objects.last()
    url = reverse("procurement:deliveries_delete", kwargs={"pk": delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_delivery_delete_view_renders(client, user, delivery):
    user = user()
    delivery = delivery()
    permission = Permission.objects.get(codename="delete_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("procurement:deliveries_delete", kwargs={"pk": delivery.delivery_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/partials/delivery_delete_view.html")


@pytest.mark.django_db
def test_delivery_delete_view_post_successful(client, user, delivery):
    user = user()
    permission = Permission.objects.get(codename="delete_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    delivery = delivery()
    url = reverse("procurement:deliveries_delete", kwargs={"pk": delivery.delivery_id})
    response = client.post(url)
    assert response.status_code == 302
    TblDeliveries.objects.filter(
        delivery_id=delivery.delivery_id
    ).exists()  # Ensure the delivery is deleted


@pytest.mark.django_db
def test_delivery_delete_view_post_successful_htmx(client, user, delivery):
    user = user()
    permission = Permission.objects.get(codename="delete_tbldeliveries")
    user.user_permissions.add(permission)
    client.force_login(user)
    delivery = delivery()
    url = reverse("procurement:deliveries_delete", kwargs={"pk": delivery.delivery_id})
    response = client.post(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert not TblDeliveries.objects.filter(
        delivery_id=delivery.delivery_id
    ).exists()  # Ensure the delivery is deleted


@pytest.mark.django_db
def test_invoice_table_view_requires_login(client):
    url = reverse("procurement:invoices_table")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_invoice_table_view_permission_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("procurement:invoices_table")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_invoice_table_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="view_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("procurement:invoices_table")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/invoices_table.html")

    # test htmx
    response_with_params = client.get(url, HTTP_HX_REQUEST="true")
    assert response_with_params.status_code == 200


@pytest.mark.django_db
def test_invoice_create_view_requires_login(client):
    url = reverse("procurement:invoices_create")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_invoice_create_view_permission_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("procurement:invoices_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_invoice_create_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="add_tblinvoices")
    user.user_permissions.add(permission)
    user = user
    client.force_login(user)
    url = reverse("procurement:invoices_create")

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/invoices_create.html")


@pytest.mark.django_db
def test_invoice_create_view_post_successful(
    client, user, purchase_order, po_line, invoice_status
):
    user = user()
    permission = Permission.objects.get(codename="add_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("procurement:invoices_create")
    po = purchase_order(po_total=100)
    po_line1 = po_line(po=po).save()
    data = {
        "invoice_no": "INV-12345",
        "invoice_date": "2023-10-01",
        "po": po.pk,
        "invoice_status": invoice_status().pk,
        "invoice_amount": po.po_total,
    }

    response = client.post(url, data)
    assert response.status_code == 302

    assert TblInvoices.objects.filter(
        invoice_no="INV-12345"
    ).exists()  # Ensure the invoice is created


@pytest.mark.django_db
def test_invoice_detail_view_requires_login(client, invoice):
    invoice = invoice()
    url = reverse("procurement:invoices_detail", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_invoice_detail_view_permission_required(client, user, invoice):
    user = user()
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_detail", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_invoice_detail_view_renders(client, user, invoice):
    user = user()
    permission = Permission.objects.get(codename="view_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_detail", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/invoices_detail.html")


@pytest.mark.django_db
def test_invoices_update_view_requires_login(client, invoice):
    invoice = invoice()
    url = reverse("procurement:invoices_update", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_invoices_update_view_permission_required(client, user, invoice):
    user = user()
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_update", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_invoices_update_view_renders(client, user, invoice):
    user = user()
    permission = Permission.objects.get(codename="change_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_update", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/invoices_create.html")


@pytest.mark.django_db
def test_invoices_update_view_post_successful(client, invoice_status, user, invoice):
    user = user()
    permission = Permission.objects.get(codename="change_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_update", kwargs={"pk": invoice.invoice_id})

    data = {
        "invoice_no": "INV-12345",
        "invoice_date": "2023-10-01",
        "po": invoice.po.po_id,
        "invoice_status": invoice_status().pk,
        "invoice_amount": 10.00,
    }

    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse(
        "procurement:invoices_detail", kwargs={"pk": invoice.invoice_id}
    )
    updated_invoice = TblInvoices.objects.get(invoice_id=invoice.invoice_id)
    assert updated_invoice.invoice_no == "INV-12345"


@pytest.mark.django_db
def test_invoices_delete_view_requires_login(client, invoice):
    invoice = invoice()
    url = reverse("procurement:invoices_delete", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_invoices_delete_view_permission_required(client, user, invoice):
    user = user()
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_delete", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_invoices_delete_view_renders(client, user, invoice):
    user = user()
    permission = Permission.objects.get(codename="delete_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_delete", kwargs={"pk": invoice.invoice_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "procurement/invoices_delete.html")


@pytest.mark.django_db
def test_invoices_delete_view_post_successful(client, user, invoice):
    user = user()
    permission = Permission.objects.get(codename="delete_tblinvoices")
    user.user_permissions.add(permission)
    client.force_login(user)
    invoice = invoice()
    url = reverse("procurement:invoices_delete", kwargs={"pk": invoice.invoice_id})

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("procurement:invoices_table")
    assert not TblInvoices.objects.filter(invoice_id=invoice.invoice_id).exists()
