from django import forms
from  django_filter_table.forms  import HTMXMultiPickerWidget
from assets.models import Tblmodel, Tbllocations
from .models import (
    AssetChangeProposal,
    CombinedBrands,
    CombinedCategories,
    CombinedModels,
    InventoryAudit,
    AuditItem,
    CatalogProposal,
)

class EmptyForm(forms.Form):
    pass

class InventoryAuditForm(forms.ModelForm):
    locations = forms.ModelMultipleChoiceField(
        queryset=Tbllocations.objects.all(),
        required=True,
    )

    class Meta:
        model = InventoryAudit
        fields = ["name", ]


class ModelProposalForm(forms.ModelForm):
    proposal_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    brand = forms.ModelChoiceField(
        queryset=CombinedBrands.objects.all(),
        required=True,
        widget=HTMXMultiPickerWidget(
            model=CombinedBrands, 
            fieldname='id',
        ),
    )
    category = forms.ModelChoiceField(
        queryset=CombinedCategories.objects.all(),
        required=True,
        widget=HTMXMultiPickerWidget(
                model=CombinedCategories, 
                fieldname='id',
        ),
    )

    class Meta:
        model = CatalogProposal
        fields = [
            "proposed_name",
            "proposed_model_number",
            "proposed_model_gtin",
            "discovered_in",
        ]

class BrandProposalForm(forms.ModelForm):

    class Meta:
        model = CatalogProposal
        fields = [
            "proposed_name",
        ]

class CategoryProposalForm(forms.ModelForm):

    class Meta:
        model = CatalogProposal
        fields = [
            "proposed_name",
        ]


class AssetChangeProposalForm(forms.Form):
    audit_item = forms.CharField(widget=forms.HiddenInput(), required=False)
    proposal_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    reason = forms.CharField(
        label="Reason for change",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
    )

    change_locationid = forms.BooleanField(
        label="Change location",
        required=False,
    )
    locationid = forms.ModelChoiceField(
        queryset=Tbllocations.objects.all(),
        required=False,
        label="New official location",
        widget=HTMXMultiPickerWidget(
            model=Tbllocations,
            fieldname='locationid'
        )

    )

    change_modelid = forms.BooleanField(
        label="Change model",
        required=False,
    )
    modelid = forms.ModelChoiceField(
        queryset=CombinedModels.objects.all(),
        required=False,
        label="New official model",
        widget=HTMXMultiPickerWidget(
            model=CombinedModels,
            fieldname='id'
        )
    )

    change_serialnumber = forms.BooleanField(
        label="Change serial number",
        required=False,
    )
    serialnumber = forms.CharField(
        label="New serial number",
        required=False,
    )

    change_customerassetnumber = forms.BooleanField(
        label="Change asset number",
        required=False,
    )
    customerassetnumber = forms.CharField(
        label="New asset number",
        required=False,
    )


    def clean(self):
        cleaned = super().clean()
        
        audit_item_id = cleaned.get('audit_item')
        if audit_item_id:
            cleaned['audit_item'] = AuditItem.objects.filter(
                asset__isnull=False, pk=audit_item_id
            ).select_related("asset").first()

        proposal_id = cleaned.get('proposal_id')
        if proposal_id:
            cleaned['proposal'] = AssetChangeProposal.objects.filter(
                pk=proposal_id
            ).first()

        selected_fields = [
            "locationid",
            "modelid",
            "serialnumber",
            "customerassetnumber",
        ]

        selected_changes = [
            field for field in selected_fields
            if cleaned.get(f"change_{field}")
        ]

        if not selected_changes:
            raise forms.ValidationError(
                "Select at least one field to change."
            )

        if cleaned.get("change_location") and not cleaned.get("location"):
            self.add_error("location", "Select a new location.")

        if cleaned.get("change_model"):
            selected_models = [
                cleaned.get("model"),
                cleaned.get("proposed_model"),
            ]
            if sum(value is not None for value in selected_models) != 1:
                raise forms.ValidationError(
                    "For a model change, select exactly one existing "
                    "model or proposed model."
                )

        changes = {}
        for fieldname in selected_fields:
            change_fieldname = f'change_{fieldname}'
            if cleaned.get(change_fieldname, False):
                changes[fieldname] = cleaned.get(fieldname)
            
        cleaned['changes'] = changes
        
        return cleaned



class NewAssetProposalForm(forms.Form):
    audit_location_id = forms.CharField(widget=forms.HiddenInput(), required=False)


    modelid = forms.ModelChoiceField(
        queryset=CombinedModels.objects.all(),
        required=False,
        label="Model",
        widget=HTMXMultiPickerWidget(
            model=CombinedModels,
            fieldname='id',
        )
    )

    serialnumber = forms.CharField(
        label="Serial number",
        required=False,
    )

    customerassetnumber = forms.CharField(
        label="Asset number",
        required=False,
    )


    def clean(self):
        cleaned = super().clean()
        

        selected_fields = [
            "modelid",
            "serialnumber",
            "customerassetnumber",
        ]

        changes = {}
        for fieldname in selected_fields:
            change_fieldname = f'change_{fieldname}'
            if cleaned.get(change_fieldname, False):
                changes[fieldname] = cleaned.get(fieldname)
            
        cleaned['changes'] = changes
        
        return cleaned
