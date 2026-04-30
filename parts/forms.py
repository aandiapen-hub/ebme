from django_select2.forms import ModelSelect2Widget, ModelSelect2MultipleWidget

from django import forms

from assets.models import Tblmodel

from .models import Tblpartslist, Tblpartsprice

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
        widget=ModelSelect2MultipleWidget(
            model=Tblmodel,
            search_fields=['modelname__icontains',
                           'brandid__brandname__icontains',
                           'categoryid__categoryname__icontains'],
            attrs={'data-placeholder': 'Select a Model', 'style': 'width: 50%;',
                   "data-minimum-input-length": 0,
                   "data-close-on-select": "false"}
        )
    )
    partid = forms.IntegerField(widget=forms.HiddenInput)