from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import TblDocuments, TblDocumentLinks, TemporaryUpload, DocumentTypes, TempUploadGroup
from django_select2.forms import (
    ModelSelect2Widget,
    ModelSelect2MultipleWidget,
)
from documents.services.documents import create_document_from_file

from assets.models import Tblbrands


class DocumentCreateForm(forms.ModelForm):
    document_bytea = forms.FileField(
        widget=forms.FileInput(attrs={"capture": "environment"})
    )

    class Meta:
        model = TblDocuments
        fields = [
            "document_name",
            "document_description",
            "document_type_id",
        ]


class LinkTemporaryDocumentForm(forms.Form):
    document_type = forms.ChoiceField(choices=DocumentTypes.choices)


class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = TblDocuments
        fields = (
            "document_name",
            "document_description",
            "document_type_id",
        )

    document_bytea = forms.FileField(required=False)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {
            "accept": "image/*",  # Accept only images
            "capture": "environment",  # Suggest rear camera on mobile
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class TempFileUploadForm(forms.ModelForm):
    files = MultipleFileField(required=True)

    def clean_files(self):
        uploaded_files = self.cleaned_data.get("files", [])
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
        max_size = 5 * 1024 * 1024  # 5 MB

        for file in uploaded_files:
            if file.content_type not in allowed_types:
                raise forms.ValidationError(
                    f"{file.name}: Unsupported file type. Allowed: JPEG, PNG."
                )

            if file.size > max_size:
                raise forms.ValidationError(
                    f"{file.name}: File size must be under 5MB."
                )
        return uploaded_files

    class Meta:
        model = TemporaryUpload
        fields = ()


class QuickScannerForm(forms.Form):
    scanned_code = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"autofocus": None, "placeholder": "Quick Search"}
        ),
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": "image/*",  # Accept only images
                "capture": "environment",  # Suggest rear camera on mobile
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        scanned_code = cleaned_data.get("scanned_code")
        file = cleaned_data.get("file")

        # allow empty
        if not file and not scanned_code:
            raise forms.ValidationError({"__all__": "at least one input required"})

        if file:
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
            max_size = 5 * 1024 * 1024  # 5 MB

            if file.content_type not in allowed_types:
                raise forms.ValidationError(
                    f"{file.name}: Unsupported file type. Allowed: JPEG, PNG."
                )

            if file.size > max_size:
                raise forms.ValidationError(
                    f"{file.name}: File size must be under 5MB."
                )

        return cleaned_data


class DocumentLinkUpdateForm(forms.ModelForm):
    class Meta:
        model = TblDocumentLinks
        fields = (
            "documentid",
            "content_type",
            "object_id",
            "customer",
        )
        widgets = {
            "documentid": ModelSelect2Widget(
                model=TblDocuments,
                search_fields=["document_name__icontains"],
                attrs={
                    "data-dropdown-parent": "#modals-here",
                    "data-placeholder": "Select Document",
                    "data-minimum-input-length": 0,
                },
            ),
            "content_type": ModelSelect2Widget(
                model=ContentType,
                search_fields=["app_label__icontains"],
                attrs={
                    "data-dropdown-parent": "#modals-here",
                    "data-placeholder": "Select Content Type",
                    "data-minimum-input-length": 0,
                },
            ),
        }


class BulkLinkDocument(forms.Form):
    document = forms.FileField(
        required=True,
        widget=forms.FileInput(
            attrs={
                "accept": "image/*",  # Accept only images
                "capture": "environment",  # Suggest rear camera on mobile
            }
        ),
    )
    document_type = forms.ChoiceField(required=True, choices=DocumentTypes.choices)
    document_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"autofocus": None, "placeholder": "Name (Optional)"}
        ),
    )
    document_description = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"autofocus": None, "placeholder": "Description (Optional)"}
        ),
    )
    source_object = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("document")

        document_name = cleaned_data["document_name"] or uploaded_file.name
        document = create_document_from_file(
            uploaded_file=uploaded_file,
            document_type_id=cleaned_data["document_type"],
            document_name=document_name,
            document_description=cleaned_data["document_description"],
        )
        cleaned_data["source_object"] = document


class EmptyForm(forms.Form):
    pass


class TempUploadGroupUpdateForm(forms.ModelForm):
    class Meta:
        model = TempUploadGroup
        fields = (
            'document_type_id',
        )


class AssetDataUpdate(forms.Form):
    GTIN = forms.CharField(required=False)
    SERIAL = forms.CharField(required=False)
    ASSET_NO = forms.CharField(required=False)
    PROD_DATE: forms.CharField(required=False)
    model_description = forms.CharField(required=False)
    brand_id = forms.ModelMultipleChoiceField(
        queryset=Tblbrands.objects.all(),
        required=False,
        widget=ModelSelect2MultipleWidget(
            model=Tblbrands,
            search_fields=['brandname'],
        )
    )

