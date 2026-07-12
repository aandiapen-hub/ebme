from django_select2.forms import ModelSelect2Widget
from documents.mixins import TempUploadUpdateFormMixin
from django_bootstrap5.widgets import RadioSelectButtonGroup

from django.core.exceptions import ValidationError
from django import forms
from assets.models import (
    Tbljob,
    Tblassets,
    Tbltesteqused,
    Tblcheckslists,
    Tbltestscarriedout,
    Tblpartsused,
    Tblcheckslists,
)
from parts.models import Tblpartslist

from utils.dynamic_formset import CustomFormsetForm

class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")  # HTML5 format
        super().__init__(*args, **kwargs)


class JobUpdateForm(TempUploadUpdateFormMixin, forms.ModelForm):
    jobid = forms.IntegerField(
        widget=forms.TextInput(attrs={"readonly": True}), label="Job ID"
    )

    class Meta:
        model = Tbljob
        fields = (
            "jobid",
            "jobtypeid",
            "technicianid",
            "jobstatusid",
            "jobstartdate",
            "jobenddate",
            "workdone",
        )

        widgets = {
            "jobenddate": DateInput(),
            "jobstartdate": DateInput(),
        }
        labels = {
            "jobtypeid": "Job Type",
            "technicianid": "Technician",
            "jobstatusid": "Job Status",
            "jobstartdate": "Start Date",
            "jobenddate": "End Date",
            "workdone": "Work Done",
        }


class TestEqUsedForm(CustomFormsetForm):
    lookup_model = Tblassets
    lookup_field = 'test_eq'
    obj_str_repr = lambda form, obj:(
                f"{obj.modelid.categoryid}-"
                f"{obj.modelid}: "
                f"{obj.serialnumber}"
            )

    class Meta:
        model = Tbltesteqused
        fields = ("test_eq",)

        widgets = {
            'test_eq': forms.HiddenInput
        }

TestEqFormset = forms.inlineformset_factory(
    Tbljob, Tbltesteqused, form=TestEqUsedForm, extra=0, can_delete=True
)


class JobCreateForm(forms.ModelForm):
    class Meta:
        model = Tbljob
        fields = (
            "assetid",
            "jobtypeid",
            "technicianid",
            "jobstatusid",
            "jobstartdate",
            "jobenddate",
            "workdone",
        )

        widgets = {
            "assetid": ModelSelect2Widget(
                model=Tblassets,
                search_fields=[
                    "assetid__icontains",
                    "customerassetnumber__icontains",
                    "serialnumber__icontains",
                ],
                attrs={
                    "data-placeholder": "Select Asset",
                    "data-minimum-input-lengtht": 0,
                },
            ),
            "jobenddate": DateInput(),
            "jobstartdate": DateInput(),
        }


class ChecklistForm(CustomFormsetForm):
    lookup_model = Tblcheckslists
    lookup_field = 'checkid'

    class Meta:
        model = Tbltestscarriedout
        fields = ("testid", "checkid", "resultid")  # Specify the fields to include in the form
        widgets = {
            "checkid": forms.HiddenInput,
            "resultid": RadioSelectButtonGroup,
        }
        labels = {
            'resultid': ''
        }


ChecklistFormset = forms.inlineformset_factory(
    Tbljob, Tbltestscarriedout, form=ChecklistForm, extra=0, can_delete=True
)

class PartsUsedForm(CustomFormsetForm):
    lookup_model = Tblpartslist
    lookup_field = 'partid'
    class Meta:
        model = Tblpartsused
        fields = ("partid", "quantity", "unitprice")  # Specify the fields to include in the form
        widgets = {
            'partid':forms.HiddenInput,
        }

PartsUsedFormset = forms.inlineformset_factory(
    Tbljob, Tblpartsused, form=PartsUsedForm, extra=0, can_delete=True
)


class JobBulkUpdateForm(forms.ModelForm):
    class Meta:
        model = Tbljob
        fields = (
            "jobtypeid",
            "technicianid",
            "jobstatusid",
            "jobstartdate",
            "jobenddate",
            "workdone",
        )

        widgets = {
            "jobenddate": DateInput(),
            "jobstartdate": DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned_data = super().clean()
        if all(value in [None, "", [], ()] for value in cleaned_data.values()):
            raise ValidationError({"__all__": "No values entered"})
