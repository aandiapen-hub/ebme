from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q


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
