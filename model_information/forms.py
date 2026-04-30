from django import forms
from assets.models import Tblbrands, Tblcategories, Tblmodel
from django_select2.forms import ModelSelect2Widget


class ModelQuickCreateForm(forms.ModelForm):
    temp_group_pk = forms.TextInput()

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
