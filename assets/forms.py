from django import forms
from .models import Tblassets, Tblmodel, Tblcustomer, TblAssetStatus, Tblppmschedules
from django_select2.forms import ModelSelect2Widget
from django.core.exceptions import ValidationError


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")  # HTML5 format
        super().__init__(*args, **kwargs)


class AssetUpdateForm(forms.ModelForm):
    assetid = forms.CharField(
        widget=forms.HiddenInput(), required=False, label="Asset ID"
    )

    class Meta:
        model = Tblassets
        fields = (
            "assetid",
            "customerassetnumber",
            "customerid",
            "serialnumber",
            "modelid",
            "softwareversion",
            "ppmscheduleid",
            "installationdate",
            "unitprice",
            "ordernumber",
            "locationid",
            "asset_status_id",
            "prod_date",
            "is_test_eq",
        )

        widgets = {
            "installationdate": DateInput(),
            "prod_date": DateInput(),
            "modelid": ModelSelect2Widget(
                model=Tblmodel,
                search_fields=[
                    "modelname__icontains",
                    "brandid__brandname__icontains",
                    "categoryid__categoryname__icontains",
                ],
                attrs={
                    "data-placeholder": "Select Model",
                    "data-minimum-input-length": 0,
                },
            ),
            "is_test_eq": forms.CheckboxInput(),
        }

        labels = {
            "customerassetnumber": "Customer Asset No.",
            "customerid": "Customer",
            "serialnumber": "Serial No.",
            "modelid": "Model",
            "softwareversion": "Software Version",
            "ppmscheduleid": "PPM Schedule",
            "installationdate": "Installation Date",
            "unitprice": "Unit Price",
            "ordernumber": "Order No.",
            "locationid": "Location",
            "asset_status_id": "Status",
            "prod_date": "Production Date",
            "is_test_eq": "Test Equipment",
        }


class AssetBulkUpdateForm(forms.Form):
    customerid = forms.ModelChoiceField(
        queryset=Tblcustomer.objects.all(), required=False, label="Customer"
    )
    modelid = forms.ModelChoiceField(
        queryset=Tblmodel.objects.all(), label="Model", required=False
    )
    softwareversion = forms.CharField(required=False, label="Software Version")
    ppmscheduleid = forms.ModelChoiceField(
        required=False, queryset=Tblppmschedules.objects.all(), label="PPM Schedule"
    )
    installationdate = forms.DateField(
        required=False,
        label="Installation Date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    unitprice = forms.DecimalField(required=False, label="Unit Price")
    ordernumber = forms.CharField(required=False, label="Order No.")
    locationid = forms.CharField(required=False, label="Location")
    asset_status_id = forms.ModelChoiceField(
        queryset=TblAssetStatus.objects.all(), required=False, label="Status"
    )
    prod_date = forms.DateField(
        required=False,
        label="Production Date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    is_test_eq = forms.NullBooleanField(
        required=False,
        label="Test Equipment",
        widget=forms.RadioSelect(
            choices=[
                ("unknown", "---"),  # or ('', '---') to map to None
                ("true", "Yes"),
                ("false", "No"),
            ]
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        if all(value in [None, "", [], ()] for value in cleaned_data.values()):
            print("clean form is not valid")
            raise ValidationError({"__all__": "No values entered"})
            print("dictionary is empty")


class AssetCreateFromFileForm(forms.Form):
    ai = forms.BooleanField(
        required=False,
        help_text="Use AI to extract non-barcode related information from images",
    )
    group = forms.CharField(widget=forms.HiddenInput, required=False)
