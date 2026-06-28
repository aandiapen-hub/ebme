from django import forms
from assets.models import Tblbrands, Tblcategories, Tbllocations, Tblmodel, Tblsites
from django_select2.forms import ModelSelect2Widget

from documents.mixins import TempUploadUpdateFormMixin
from model_information.models import EquipmentConfigurationScope


class ModelCreateForm(forms.ModelForm):
    class Meta:
        model = Tblmodel
        fields = "__all__"

        widgets = {
            "brandid": ModelSelect2Widget(
                model=Tblbrands,
                search_fields=["brandname__icontains"],
                attrs={
                    "data-placeholder": "Select Brand",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true",
                },
            ),
            "categoryid": ModelSelect2Widget(
                model=Tblcategories,
                search_fields=[
                    "categoryname__icontains",
                    "categorydescription__icontains",
                    "gmdnname__icontains",
                ],
                attrs={
                    "data-placeholder": "Select Category",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true",
                },
            ),
        }


class ModelUpdateForm(TempUploadUpdateFormMixin,forms.ModelForm):
    class Meta:
        model = Tblmodel
        fields = "__all__"

        widgets = {
            "brandid": ModelSelect2Widget(
                model=Tblbrands,
                search_fields=["brandname__icontains"],
                attrs={
                    "data-placeholder": "Select Brand",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true",
                },
            ),
            "categoryid": ModelSelect2Widget(
                model=Tblcategories,
                search_fields=[
                    "categoryname__icontains",
                    "categorydescription__icontains",
                    "gmdnname__icontains",
                ],
                attrs={
                    "data-placeholder": "Select Category",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true",
                },
            ),
        }

class BrandBulkUpdateForm(forms.ModelForm):
    class Meta:
        model = Tblbrands
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class ModelBulkUpdateForm(forms.ModelForm):
    class Meta:
        model = Tblmodel
        fields = ("brandid", "categoryid")

        widgets = {
            "brandid": ModelSelect2Widget(
                model=Tblbrands,
                search_fields=["brandname__icontains"],
                attrs={
                    "data-placeholder": "Select Brand",
                    "data-minimum-input-length": 0,
                },
            ),
            "categoryid": ModelSelect2Widget(
                model=Tblcategories,
                search_fields=[
                    "categoryname__icontains",
                    "categorydescription__icontains",
                    "gmdnname__icontains",
                ],
                attrs={
                    "data-placeholder": "Select Category",
                    "data-minimum-input-length": 0,
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

class ConfigurationScopeCreateForm(forms.ModelForm):

    class Meta:
        model = EquipmentConfigurationScope
        fields = '__all__'

        widgets = {
            'site': ModelSelect2Widget(
                model=Tblsites,
                search_fields=["sitename__icontains"],
                attrs={
                    "data-placeholder": "Select Site",
                    "data-minimum-input-length": 0,
                },
            ),
            'location': ModelSelect2Widget(
                model=Tbllocations,
                search_fields=["locationname__icontains"],
                dependent_fields={'site': 'siteid'},
                attrs={
                    "data-placeholder": "Select location",
                    "data-minimum-input-length": 0,
                },
            ),

        }
