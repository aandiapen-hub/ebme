from django_select2.forms import ModelSelect2Widget
from django.utils.dateparse import parse_date, parse_datetime
from datetime import datetime, date

from django.core.exceptions import ValidationError
from django import forms
from assets.models import (Tbljob, Tbltesteqused,
                            Tblcheckslists,Tbltestscarriedout,
                            Tblpartsused,
)
from django.db.models import Q
from parts.models import Tblpartslist
from parts.models import TblPartModel


class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, *args, **kwargs):
            kwargs.setdefault('format', '%Y-%m-%d')  # HTML5 format
            super().__init__(*args, **kwargs)
            

class JobUpdateForm(forms.ModelForm):
    jobid = forms.IntegerField(widget=forms.TextInput(
        attrs={'readonly': True }),
        label="Job ID")

    class Meta:
        model = Tbljob
        fields = ("jobid","jobtypeid","technicianid","jobstatusid",
                  "jobstartdate","jobenddate","workdone")

        widgets = {
            "jobenddate":DateInput(),
            "jobstartdate":DateInput(),
        }
        labels = {
            "jobtypeid": "Job Type",
            "technicianid": "Technician",
            "jobstatusid": "Job Status",
            "jobstartdate": "Start Date",
            "jobenddate": "End Date",
            "workdone": "Work Done",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original = {}
        if self.instance and self.instance.pk:
            for field_name in self.fields:
                if hasattr(self.instance, f'{field_name}_id'):
                    original = getattr(self.instance, f'{field_name}_id', None)
                else:
                    original = getattr(self.instance, field_name)

                new = self.initial.get(field_name)
                # normalise date values
                if isinstance(original, date):
                    if isinstance(original, datetime):
                        new_parsed = parse_datetime(new) if isinstance(new, str) else new
                    else:
                        new_parsed = parse_date(new) if isinstance(new, str) else new
                else:
                    new_parsed = new
                if new_parsed != original:
                    self.original[field_name] = getattr(self.instance, field_name)


class AddTestEquipmentToJobForm(forms.ModelForm):

    class Meta:
        model = Tbltesteqused
        fields = ('test_eq',)

class JobCreateForm(forms.ModelForm):
    
    class Meta:
        model = Tbljob
        fields = ("assetid","jobtypeid","technicianid","jobstatusid",
                  "jobstartdate","jobenddate","workdone")

        widgets = {
            "jobenddate":DateInput(),
            "jobstartdate":DateInput(),
        }

class TestCarriedOutForm(forms.ModelForm):

    class Meta:
        model = Tbltestscarriedout
        fields = ('checkid', 'resultid')  # Specify the fields to include in the form
        widgets = {
            'checkid': ModelSelect2Widget(
                model=Tblcheckslists,
                search_fields=['testname__icontains','test_description__icontains','modelid__modelname__icontains'],
                attrs={
                    'data-dropdown-parent': '#modals-here',
                    'data-placeholder': 'Select Test',
                    'data-minimum-input-length': 0}),
            'resultid': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }




class SparePartsUsedUpdateForm(forms.ModelForm):

    class Meta:
        model = Tblpartsused
        fields = ('partid', 'quantity','unitprice')  # Specify the fields to include in the form
        widgets = {
            'partid': ModelSelect2Widget(
                model=TblPartModel,
                search_fields=['part_number__icontains','short_name__icontains','description__icontains'],
                attrs={
                    'data-placeholder': 'Select Spare Part',
                    'data-minimum-input-length': 0})
        }
 


class SparePartsUsedCreateForm(forms.ModelForm):

    class Meta:
        model = Tblpartsused
        fields = ('partid', 'quantity')  # Specify the fields to include in the form
        widgets = {
            'partid': ModelSelect2Widget(
                model=TblPartModel,
                search_fields=['part_number__icontains','short_name__icontains','description__icontains'],
                attrs={
                    'data-dropdown-parent': '#modals-here',
                    'data-placeholder': 'Select Spare Part',
                    'data-minimum-input-length': 0})
        }

    def __init__(self, *args, **kwargs):

        self.modelid = kwargs.pop('modelid', None) 
        super().__init__(*args, **kwargs)

        if  self.modelid:
            parts_ids = TblPartModel.objects.filter(model=self.modelid).values_list('part')
            parts = Tblpartslist.objects.filter(partid__in=parts_ids)
            active_parts = parts.filter(~Q(inactive=True) | Q(inactive__isnull=True))
            self.fields['partid'].queryset = active_parts

class JobBulkUpdateForm(forms.ModelForm):

    class Meta:
        model = Tbljob
        fields = ("jobtypeid","technicianid","jobstatusid",
                  "jobstartdate","jobenddate","workdone")

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
            print("clean form is not valid")
            raise ValidationError({"__all__": "No values entered"})
            print("dictionary is empty")
