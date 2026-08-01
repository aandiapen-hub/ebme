from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.forms import BooleanField, HiddenInput, UUIDField
from django.urls import reverse

from documents.services.document_parser import temp_group_resolver
from documents.models import TempUploadGroup
from documents.services.documents import save_temp_files
from documents.services.payloads import (
    apply_payload_to_initial,
    apply_payload_to_context,
)
from django.utils.dateparse import parse_date, parse_datetime
from datetime import datetime, date

class DocumentLinkPermissionMixin(PermissionRequiredMixin):

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_staff:
            return qs

        user_customerid = getattr(self.request.user, "customerid", None)
        if user_customerid is None:
            return qs.none()

        return qs.filter(Q(customer_id=user_customerid) | Q(customer_id__isnull=True))


class TempUploadMixin:
    initial_mapper = None

    def get_temp_group_id(self):
        return (
            self.request.POST.get("temp_group_id")
            or self.request.GET.get("temp_group_id")
        )

    def get_initial_mapper(self):
        return self.initial_mapper

    def get_temp_group(self):
        temp_group_id = self.get_temp_group_id()

        if not temp_group_id:
            return None

        return TempUploadGroup.objects.filter(
            pk=temp_group_id
        ).first()

    def apply_temp_payload_to_initial(self, initial):
        return apply_payload_to_initial(
            self.get_temp_group_id(),
            initial=initial,
            initial_mapper=self.get_initial_mapper()
        )

    def apply_temp_payload_to_context(self, context):
        return apply_payload_to_context(
            self.get_temp_group_id(),
            context=context,
            context_mapper=self.get_initial_mapper()
        )

    def get_initial(self):
        initial = super().get_initial()

        # populate from query params
        initial.update(self.request.GET.items())

        # populate from payload
        initial = self.apply_temp_payload_to_initial(initial)

        return initial

    def save_temp_files(
        self,
        form,
        content_object,
        file_name=None,
    ):
        temp_group_id = self.get_temp_group_id()
        self.delete_temp_group = form.cleaned_data.get('delete_temp_files_after_save', False)

        if not temp_group_id:
            return

        if form.cleaned_data.get('save_and_attach_document', False):
            save_temp_files(
                group=temp_group_id,
                content_object=content_object,
                file_name=file_name
            )
        if self.delete_temp_group:
            TempUploadGroup.objects.get(pk=temp_group_id).delete()

    def has_temp_group(self):
        return self.get_temp_group_id() is not None

    # Add fields for saving and/or deleting temp documents
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.has_temp_group():
            form.fields['save_and_attach_document'] = BooleanField(
                required=False,
                initial=False,
                label='Save and Attach uploaded documents'
            )
            form.fields['delete_temp_files_after_save'] = BooleanField(
                required=False,
                initial=False,
                label='Delete Temporary files after safe'
            )
            form.fields['temp_group_id'] = UUIDField(
                required=True,
                initial=self.get_temp_group_id(),
                widget=HiddenInput,
            )
        return form

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # populate from payload
        context = self.apply_temp_payload_to_context(context=context)
        context['temp_group'] = self.get_temp_group()

        return context

    def get_success_url(self):
        temp_id = self.get_temp_group_id()
        if temp_id and not self.delete_temp_group:
            return reverse('documents:temp_group', kwargs={'pk': temp_id})
        else:
            return reverse(self.success_url_app_view, kwargs={'pk': self.object.pk})

    def after_save(self, form):
        self.save_temp_files(form, self.object)
        temp_id = self.get_temp_group_id()
        if temp_id:
            temp_group_resolver(temp_id)


class TempUploadUpdateFormMixin:
    """
    Adds 'self.original' dict containing fields that changed compared 
    to the model instance.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original = {}
        self._compute_original_values()

    def _get_instance_value(self, field):
        """
        Handles FK *_id vs attribute access.
        """
        if hasattr(self.instance, f"{field}_id"):
            return getattr(self.instance, f"{field}_id")
        if hasattr(self.instance, field):
            return getattr(self.instance, field)

    def _normalise_date(self, value, original):
        """
        Normalise date values to enable consistent comparison
        """
        if isinstance(original, datetime):
            return parse_datetime(value) if isinstance(value, str) else value

        if isinstance(original, date):
            return parse_date(value) if isinstance(value, str) else value

        return value

    def _compute_original_values(self):

        for field_name in self.fields:
            original = self._get_instance_value(field_name)
            new = self.initial.get(field_name)

            new_normalised = self._normalise_date(new, original)

            if new_normalised != original:
                self.original[field_name] = original

