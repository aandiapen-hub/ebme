from django import forms
from  django_filter_table.forms  import HTMXMultiPickerWidget
from assets.models import Tblmodel, Tbllocations
from .models import (
    CombinedBrands,
    CombinedCategories,
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
    audit_item = forms.HiddenInput()

    reason = forms.CharField(
        label="Reason for change",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
    )

    change_location = forms.BooleanField(
        label="Change location",
        required=False,
    )
    location = forms.ChoiceField(
        required=False,
        label="New official location",
        widget=HTMXMultiPickerWidget(
            model=Tbllocations,
            fieldname='locationid'
        )

    )

    change_model = forms.BooleanField(
        label="Change model",
        required=False,
    )
    model = forms.ModelChoiceField(
        queryset=Tblmodel.objects.none(),
        required=False,
        label="New official model",
        widget=HTMXMultiPickerWidget(
            model=Tblmodel,
            fieldname='modelid'
        )
    )
    proposed_model = forms.ModelChoiceField(
        queryset=CatalogProposal.objects.filter(
            entity_type=CatalogProposal.EntityType.MODEL,
            status=CatalogProposal.Status.PROPOSED,
        ),
        required=False,
        label="New proposed model",
    )

    change_serial_number = forms.BooleanField(
        label="Change serial number",
        required=False,
    )
    serial_number = forms.CharField(
        label="New serial number",
        required=False,
    )

    change_asset_number = forms.BooleanField(
        label="Change asset number",
        required=False,
    )
    asset_number = forms.CharField(
        label="New asset number",
        required=False,
    )

    widget = {
            }

    def clean(self):
        cleaned = super().clean()

        
        cleaned['audit_item'] = AuditItem.objects.filter(
            asset__isnull=False, pk=cleaned.get('audit_item')
        ).select_related("asset").first(),

        selected_fields = [
            "location",
            "model",
            "serial_number",
            "asset_number",
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

        return cleaned
