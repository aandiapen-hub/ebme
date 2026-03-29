
from django import forms

from .models import TblDocuments, TblDocumentTypes, TemporaryUpload


class DocumentLinkCreateForm(forms.ModelForm):
    document_bytea = forms.FileField(
        widget=forms.FileInput(attrs={'capture': 'environment'})
    )

    class Meta:
        model = TblDocuments
        fields = [
            'document_name',
            'document_description',
            'document_type_id',
        ]


class LinkTemporaryDocumentForm(forms.Form):
    document_type = forms.ModelChoiceField(queryset=TblDocumentTypes.objects.all())


class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = TblDocuments
        fields = "__all__"

    document_bytea = forms.FileField(required=False)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {
            'accept': 'image/*',           # Accept only images
            'capture': 'environment',      # Suggest rear camera on mobile
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
        uploaded_files = self.cleaned_data.get('files', [])
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
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
        widget=forms.TextInput(attrs={'autofocus': None, 'placeholder':'Quick Search'}),
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
                                'accept': 'image/*',           # Accept only images
                                'capture': 'environment',      # Suggest rear camera on mobile
                                }
                               )
    )

    def clean(self):
        cleaned_data = super().clean()
        scanned_code = cleaned_data.get('scanned_code')
        file = cleaned_data.get('file')

        # allow empty
        if not file and not scanned_code:
            raise forms.ValidationError(
                {'__all__': 'at least one input required'}
            )

        if file:
            allowed_types = ['image/jpeg', 'image/png','image/jpg','application/pdf']
            max_size = 5 * 1024 * 1024  # 5 MB

            if file.content_type not in allowed_types:
                raise forms.ValidationError(
                    f"{file.name}: Unsupported file type. Allowed: JPEG, PNG."
                    )

            if file.size > max_size:\
                raise forms.ValidationError(
                    f"{file.name}: File size must be under 5MB."
                )

        return cleaned_data
