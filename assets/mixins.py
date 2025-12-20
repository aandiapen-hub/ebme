from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied


class CustomerAssetPermissionMixin(PermissionRequiredMixin):
    """
    Checks permission by customer_id for object-level access.
    """
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if self.request.user.is_staff:
            return obj
        else:
            # Check if the user has access to this object based on customerid
            if obj.customerid != self.request.user.customerid:
                raise PermissionDenied("You do not have permission to access this asset!!!.")
            return obj
    """
    Combines permission checking with queryset filtering by customer_id.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        else:        
            customerid = getattr(self.request.user, 'customerid', None)
            if customerid is not None:
                return qs.filter(customerid=customerid)
            raise PermissionDenied("You do not have permission to access this asset!!!.")
