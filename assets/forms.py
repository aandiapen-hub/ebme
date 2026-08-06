from django import forms
from django.db.models import CommaSeparatedIntegerField
from .models import(
    Tblassets,
    Tblmodel,
    Tblcustomer,
    TblAssetStatus,
    Tblppmschedules,
    Tbltechnicianlist
)
from django_select2.forms import ModelSelect2Widget
from django.core.exceptions import ValidationError
from model_information.models import EquipmentConfiguration, Software, SoftwareModel

from documents.mixins import TempUploadUpdateFormMixin

class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")  # HTML5 format
        super().__init__(*args, **kwargs)


class AssetUpdateForm(TempUploadUpdateFormMixin, forms.ModelForm):
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
            "ppmscheduleid": "PPM Schedule",
            "installationdate": "Installation Date",
            "unitprice": "Unit Price",
            "ordernumber": "Order No.",
            "locationid": "Location",
            "asset_status_id": "Status",
            "prod_date": "Production Date",
            "is_test_eq": "Test Equipment",
        }

    def __init__(self, acceptance=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if acceptance:

            self.fields['create_acceptance_job'] = forms.BooleanField(
                required=False,
                initial=False,
                label='Create Acceptance Job'
            )
            self.fields['technicianid'] = forms.ModelChoiceField(
                queryset=Tbltechnicianlist.objects.all(),
                label='Technician',
                required=False
                )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('create_acceptance_job', False) and not cleaned_data.get('technicianid', False):
            raise ValidationError({
                'technicianid': 'Select a Technician name for acceptance job'
            })
            
        return cleaned_data


class AssetBulkUpdateForm(forms.Form):
    customerid = forms.ModelChoiceField(
        queryset=Tblcustomer.objects.all(), required=False, label="Customer"
    )
    modelid = forms.ModelChoiceField(
        queryset=Tblmodel.objects.all(),
        required=False,
        widget=ModelSelect2Widget(
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
            raise ValidationError({"__all__": "No values entered"})


class SetEquipmentSoftwareForm(forms.Form):
    software = forms.ModelChoiceField(
        queryset=Software.objects.all(),
        required=True,
        widget=ModelSelect2Widget(
            model=Software,
            search_fields=['brand__icontains','name__icontains'],
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "Select an option",
                "data-close-on-select": "false",
            }
        )
    )

    equipment = forms.ModelChoiceField(
        queryset=Tblassets.objects.all(),
        required=True,
        widget=ModelSelect2Widget(
            model=Tblassets,
            search_fields=['serialnumber__icontains'],
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "Select an option",
                "data-close-on-select": "false",
            }
        )
    )
    
    def __init__(self, *args, **kwargs):
        equipment_id = kwargs.pop('equipment_id', None)
        super().__init__(*args, **kwargs)
        if equipment_id:
            equipment = Tblassets.objects.get(pk=equipment_id)
            compatible_software_ids = equipment.modelid.supported_software.all().values_list('software',flat=True)
            compatible_software = Software.objects.filter(pk__in=compatible_software_ids)

            self.fields['equipment'].initial = equipment_id

            self.fields['software'].queryset = compatible_software
            self.fields['software'].initial = compatible_software.last()


class SetEquipmentConfigurationForm(forms.Form):
    configuration = forms.ModelChoiceField(
        queryset=EquipmentConfiguration.objects.all(),
        required=True,
        widget=ModelSelect2Widget(
            model=EquipmentConfiguration,
            search_fields=['brand__icontains','name__icontains'],
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "Select an option",
                "data-close-on-select": "false",
            }
        )
    )

    equipment = forms.ModelChoiceField(
        queryset=Tblassets.objects.all(),
        required=True,
        widget=ModelSelect2Widget(
            model=Tblassets,
            search_fields=['serialnumber__icontains'],
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "Select an option",
                "data-close-on-select": "false",
            }
        )
    )
    
    def __init__(self, *args, **kwargs):
        equipment_id = kwargs.pop('equipment_id', None)
        super().__init__(*args, **kwargs)
        if equipment_id:
            equipment = Tblassets.objects.get(pk=equipment_id)
            required_config = EquipmentConfiguration.objects.resolve(equipment)

            self.fields['equipment'].initial = equipment_id

            if required_config:
                self.fields['configuration'].initial = required_config

class ReplicateAssetForm(forms.Form):
    pass
