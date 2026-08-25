from django import forms
from assets.models import Tblbrands, Tblmodel

from documents.mixins import TempUploadUpdateFormMixin
from htmx_select.forms import HTMXMultiPickerWidget
from model_information.models import EquipmentConfigurationScope


class ModelCreateForm(forms.ModelForm):
    class Meta:
        model = Tblmodel
        fields = "__all__"

        widgets = {
            "brandid": HTMXMultiPickerWidget(
                model=Tblmodel,
                fieldname='brandid'
            ),
            "categoryid": HTMXMultiPickerWidget(
                model=Tblmodel,
                fieldname='categoryid'
            ),
        }

class ModelCopyForm(forms.Form):
    model_id = forms.CharField(widget=forms.HiddenInput())
    gtin = forms.CharField(max_length=14)


class ModelUpdateForm(TempUploadUpdateFormMixin,forms.ModelForm):
    class Meta:
        model = Tblmodel
        fields = "__all__"

        widgets = {
            "brandid": HTMXMultiPickerWidget(
                model=Tblmodel,
                fieldname='brandid'
            ),
        "categoryid": HTMXMultiPickerWidget(
                model=Tblmodel,
                fieldname='categoryid'
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
            "brandid": HTMXMultiPickerWidget(
                model=Tblmodel,
                fieldname='brandid'
            ),
            "categoryid": HTMXMultiPickerWidget(
                model=Tblmodel,
                fieldname='categoryid'
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
            'site': HTMXMultiPickerWidget(
                model=EquipmentConfigurationScope,
                fieldname='site'
            ),
            'location': HTMXMultiPickerWidget(
                model=EquipmentConfigurationScope,
                fieldname='location'
            ),

        }

class AddNewConfigVersionForm(forms.Form):
    pass

class AddNewSoftwareVersionForm(forms.Form):
    new_version = forms.CharField(max_length=50)
