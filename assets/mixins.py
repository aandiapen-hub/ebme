from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied


class CustomerAssetPermissionMixin(PermissionRequiredMixin):
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
            return qs.none()
