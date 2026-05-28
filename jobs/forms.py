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
from django.db.models import Q
from parts.models import Tblpartslist
from parts.models import TblPartModel


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


class TestEqUsedForm(forms.ModelForm):
    class Meta:
        model = Tbltesteqused
        fields = ("test_eq",)

        widgets = {
            'test_eq': forms.HiddenInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        readonly_fields = [
            'test_eq',
            
        ]

        test_eq = getattr(self.instance, "test_eq", None)

        if test_eq:
            self.fields['test_eq'].label = (
                f"{test_eq.modelid.categoryid}-"
                f"{test_eq.modelid}: "
                f"{test_eq.serialnumber}"
            )


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


class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Tbltestscarriedout
        fields = ("checkid", "resultid")  # Specify the fields to include in the form
        widgets = {
            "checkid": forms.HiddenInput,
            "resultid": RadioSelectButtonGroup,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        readonly_fields = [
            'checkid',
        ]

        check = getattr(self.instance, "checkid", None)

        if not check:
            check_id = self.initial.get("checkid")
            if check_id:
                obj = Tblcheckslists.objects.filter(pk=check_id).first()
                self.fields['checkid'].label = obj

        if check:
            print('labels being added')
            self.fields['checkid'].label = self.instance.checkid
            self.fields['resultid'].label = ''

ChecklistFormset = forms.inlineformset_factory(
    Tbljob, Tbltestscarriedout, form=ChecklistForm, extra=0, can_delete=True
)


class PartsUsedForm(forms.ModelForm):
    class Meta:
        model = Tblpartsused
        fields = ("partid", "quantity", "unitprice")  # Specify the fields to include in the form
        widgets = {
            "partid": forms.HiddenInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        readonly_fields = [
            'partid',
        ]

        '''
        if self.modelid:
            parts_ids = TblPartModel.objects.filter(model=self.modelid).values_list(
                "part"
            )
            parts = Tblpartslist.objects.filter(partid__in=parts_ids)
            active_parts = parts.filter(~Q(inactive=True) | Q(inactive__isnull=True))
            self.fields["partid"].queryset = active_parts

        '''
        part = getattr(self.instance, "partid", None)
        if part:
            self.fields['partid'].label = (
                    f"{self.instance.partid.short_name}- "
                    f"{self.instance.partid.part_number}"
            )

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
