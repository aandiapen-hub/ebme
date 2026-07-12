from django import forms
from .models import (
    TblInvoices,
    TblPurchaseOrder,
    TblSuppliers,
    TblPoLines,
    TblDeliveries,
    TblDeliveryLines,
)
from parts.models import Tblpartslist
from django.forms import BaseInlineFormSet

from utils.dynamic_formset import CustomFormsetForm
from django_select2.forms import ModelSelect2Widget
from django.forms import inlineformset_factory


class PoLineForm(CustomFormsetForm):
    lookup_model = Tblpartslist
    lookup_field = 'item'

    class Meta:
        model = TblPoLines
        fields = ["item", "qty_ordered", "line_description", "unit_price", "vat"]
        widgets = {
            "item": forms.HiddenInput,
            "vat": forms.HiddenInput,
        }


PoLineFormset = inlineformset_factory(
    TblPurchaseOrder,
    TblPoLines,
    form=PoLineForm,
    extra=0,
    can_delete=True,
)


class PoCreateForm(forms.ModelForm):
    class Meta:
        model = TblPurchaseOrder
        fields = ["supplier", "date_raised", "ship_to_add", "order_status"]

        widgets = {
            "supplier": ModelSelect2Widget(
                model=TblSuppliers,
                search_fields=[
                    "supplier_name__icontains",
                ],
                attrs={
                    "data-placeholder": "Select Supplier",
                    "data-minimum-input-length": 3,
                },
            ),
        }


class DeliveryCreateForm(forms.ModelForm):
    class Meta:
        model = TblDeliveries
        fields = ["po", "delivery_date", "delivery_note_number"]

        widgets = {"delivery_date": forms.DateInput(attrs={"type": "date"})}

        labels = {
            "po": "Purchase Order",
            "delivery_date": "Delivery Date",
            "delivery_note_number": "Delivery Note",
        }


class DeliveryLineForm(forms.ModelForm):
    class Meta:
        model = TblDeliveryLines
        fields = ["delivery", "item", "qty"]

        labels = {"qty_ordered": "qty"}

    def __init__(self, *args, **kwargs):
        self.po = kwargs.pop("po", None)
        super().__init__(*args, **kwargs)
        if self.po:
            # Step 1: Get relevant item IDs from the view
            items = TblPoLines.objects.filter(po_id=self.po).values_list(
                "item", flat=True
            )

            # Step 2: Filter the queryset for the 'item' field
            self.fields["item"].queryset = Tblpartslist.objects.filter(partid__in=items)
        else:
            # Optional: fallback queryset if no PO provided
            self.fields["item"].queryset = Tblpartslist.objects.all()

        for name, field in self.fields.items():
            if not isinstance(field.widget, ModelSelect2Widget):
                field.widget.attrs.update({"class": "form-control"})


class DeliveryLineBaseFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.po = kwargs.pop("po", None)
        self.extra = kwargs.pop("extra", 1)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        # Pass po to each form when it’s constructed
        kwargs["po"] = self.po
        return super()._construct_form(i, **kwargs)


DeliveryLineFormset = inlineformset_factory(
    TblDeliveries,
    TblDeliveryLines,
    form=DeliveryLineForm,
    formset=DeliveryLineBaseFormSet,
    can_delete=True,
)


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")  # HTML5 format
        super().__init__(*args, **kwargs)


class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model = TblInvoices
        fields = (
            "invoice_no",
            "invoice_date",
            "po",
            "invoice_due_date",
            "invoice_status",
            "fully_paid_date",
            "invoice_amount",
            "creation_date",
        )

        widgets = {
            "invoice_date": DateInput(),
            "invoice_due_date": DateInput(),
            "fully_paid_date": DateInput(),
        }
        labels = {}

