from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from assets.models import Tbljob, Tblassets
from django.shortcuts import get_object_or_404

class CustomerJobPermissionMixin(PermissionRequiredMixin):
    def dispatch(self, request, *args, **kwargs):        
        # Get customerid from logged-in user
        customerid = getattr(request.user, 'customerid', None)

        # Fetch jobid from URL kwargs
        jobid = self.kwargs.get('jobid') or request.GET.get("jobid") or self.kwargs.get('pk')
        assetid = self.request.GET.get('assetid')   # for create view
        if request.user.is_staff:
            # You can fetch the related Tbljob object here
            
            if jobid:
                job = get_object_or_404(Tbljob,jobid=jobid)

            elif assetid:
                asset = get_object_or_404(Tblassets,assetid=assetid)
                
            # If all good, continue normally
            return super().dispatch(request, *args, **kwargs)

        else:
            if customerid is None:                
                raise PermissionDenied("Invalid access - User not linked to any customer.")

            if jobid:
                try:
                    job = Tbljob.objects.select_related('assetid__customerid').get(jobid=jobid)
                except Tbljob.DoesNotExist:
                    raise PermissionDenied("Job does not exist.")
                if job.assetid.customerid != customerid:
                    raise PermissionDenied("You don't have permission for this job.")

            elif assetid:
                
                try:
                    asset = Tblassets.objects.get(assetid=assetid)
                except Tblassets.DoesNotExist:
                    raise PermissionDenied("Asset does not exist.")
                if asset.customerid != customerid:
                    raise PermissionDenied("You don't have permission for this asset.")

            # If all good, continue normally
            return super().dispatch(request, *args, **kwargs)

    """
    Combines permission checking with queryset filtering by customer_id.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        else:
            customerid = getattr(self.request.user, 'customerid', None)
            if customerid is None:
                return self.model.objects.none()
            return qs.filter(assetid__customerid=customerid)
    
    


class CustomerJobChildPermissionMixin(PermissionRequiredMixin):
    """
    Combines permission checking with queryset filtering by customer_id.
    """
    
    def dispatch(self, request, *args, **kwargs):
        try:
            job = self.get_object()
            jobid = job.jobid.jobid
        except:
            jobid = self.kwargs.get('jobid') or request.GET.get("jobid")
        self.jobid = jobid

        job = Tbljob.objects.get(jobid=jobid)
            

        
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        else:
            # Get customerid from logged-in user
            customerid = getattr(request.user, 'customerid', None)
            
            # Fetch jobid from URL kwargs
            
            if customerid is None or jobid is None:
                raise PermissionDenied("Invalid access - missing customer or job.")


            # Now check if job belongs to user's customer
            if job.assetid.customerid != customerid:
                raise PermissionDenied("You don't have permission for this job.")
            
            # If all good, continue normally
            return super().dispatch(request, *args, **kwargs)




class CustomerJobListPermissionMixin(PermissionRequiredMixin):
    """
    Combines permission checking with queryset filtering by customer_id.
    """
    def get_queryset(self):

        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        else:
            customerid = getattr(self.request.user, 'customerid', None)
            if customerid is None:
                return self.model.objects.none()
            
            return qs.filter(assetid__customerid=customerid)