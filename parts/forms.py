from  django_filter_table.forms  import HTMXMultiPickerWidget

from django import forms

from assets.models import Tblmodel

from .models import TblPartModel, Tblpartslist, Tblpartsprice

class AddPartPrice(forms.ModelForm):
    
    class Meta:
        model = Tblpartsprice
        fields = ("price","partid","effectivedate")
        widgets = {
            'price':forms.NumberInput(attrs={'autofocus': True, 'type':'number'}),
            'partid': forms.HiddenInput(),
            'effectivedate': forms.HiddenInput()
        }

class UpdatePartPrice(forms.ModelForm):
    
    class Meta:
        model = Tblpartsprice
        fields = ("price","partid","effectivedate")
        widgets = {
            'partid': forms.HiddenInput(),
            'effectivedate': forms.DateInput(attrs={'type':'date'})
        }

class PartsBulkUpdateForm(forms.ModelForm):

    class Meta:
        model = Tblpartslist
        fields = ('supplier_id', 'inactive')

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values():
            field.required = False

class CreatePartModelLinkForm(forms.Form):
    models = forms.ModelMultipleChoiceField(
        queryset=Tblmodel.objects.all(),
        widget=HTMXMultiPickerWidget(
            model=TblPartModel,
            fieldname='model',
            multiple=True,
        )
    )
    partid = forms.IntegerField(widget=forms.HiddenInput)
