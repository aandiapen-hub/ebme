from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms import BooleanField, HiddenInput, UUIDField

from documents.models import TempUploadGroup
from documents.views import save_temp_files
from documents.services.payloads import apply_payload_to_initial

class DocumentLinkPermissionMixin(PermissionRequiredMixin):
    def check_object_permissions(self, obj):
        user_customerid = getattr(self.request.user, "customerid", None)
        is_user_staff = self.request.user.is_staff
        object_customerid = obj.customer_id

        if not is_user_staff:
            if user_customerid is None:
                raise PermissionDenied("User not associated with any customer.")
            if user_customerid != object_customerid:
                raise PermissionDenied("User cannot access this document")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.check_object_permissions(obj)  # Manually call here
        return obj

    def get_queryset(self):
        qs = super().get_queryset()
        user_customerid = getattr(self.request.user, "customerid", None)

        if self.request.user.is_staff:
            return qs

        if user_customerid is None:
            return qs.none()

        return qs.filter(Q(customerid=user_customerid) | Q(customerid__isnull=True))


class TempUploadMixin:

    def get_temp_group_id(self):
        return (
            self.request.POST.get("temp_group_id")
            or self.request.GET.get("temp_group_id")
        )

    def get_temp_group(self):
        temp_group_id = self.get_temp_group()

        if not temp_group_id:
            return None

        return TempUploadGroup.objects.filter(
            pk=temp_group_id
        ).first()

    def add_temp_group_to_context(self, context):
        temp_group = self.get_temp_group()

        if temp_group:
            context['temp_group'] = temp_group

        return context

    def apply_temp_payload_to_initial(self, initial):
        return apply_payload_to_initial(
            self.get_temp_group_id(),
            initial=initial
        )
        return initial

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
        print("*********8saving tempfile")
        temp_group_id = self.get_temp_group_id()

        print('temp group id', temp_group_id)
        if not temp_group_id:
            return

        if form.cleaned_data.get('save_and_attach_document', False):
            save_temp_files(
                group=temp_group_id,
                content_object=content_object,
                file_name=file_name
            )

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
            form.fields['temp_group_id'] = UUIDField(
                required=True,
                initial=self.get_temp_group_id(),
                widget=HiddenInput,
            )
        return form


