
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, FieldError

from .models import DocumentsView, TblDocuments


class DocumentPermissionMixin(PermissionRequiredMixin):

        
    def check_object_permissions(self, obj):
        
        if self.request.user.is_staff:
            pass 

        else:

            # Get customerid from logged-in user
            user_customerid = getattr(self.request.user, 'customerid', None)
            if not user_customerid:
                raise PermissionDenied("User not associated with any customer.")
            
            try:
            #get the document link object for update/delete views
                if isinstance(obj, DocumentsView):
                    document_link = DocumentsView.objects.get(document_link_id=obj.document_link_id) #document link object
                    document_customer_ids = [document_link.customerid_id]
                else:
                    document_links = DocumentsView.objects.filter(document_id=obj.document_id) #document link objects
                    document_customer_ids = list(document_links.values_list('customerid_id', flat=True))
            except:
            #get the document links for view/create views

                link_table = self.kwargs.get('link_table') or self.request.GET.get("link_table")
                link_row = self.kwargs.get('link_row') or self.request.GET.get("link_row")

                document_link_qs = DocumentsView.objects.filter(link_table=link_table, link_row=link_row)
                document_links_customerid = list(document_link_qs.values_list('customerid_id', flat=True))
                
                if user_customerid.customerid not in document_links_customerid:
                    raise PermissionDenied("You don't have permission for this job.")
                
            else:
                if user_customerid.customerid not in document_customer_ids:
                    raise PermissionDenied("You don't have permission for this job.")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.check_object_permissions(obj)  # Manually call here
        return obj
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        else:
            customerid = getattr(self.request.user, 'customerid', None)
            if customerid is not None:
                if qs.model == DocumentsView:
                    return qs.filter(customerid=customerid)
                elif qs.model == TblDocuments:
                    # If the model doesn't have a customerid field, return empty queryset
                    from django.db.models import Q

                    document_ids = list(
                        DocumentsView.objects
                        .filter(Q(customerid=customerid) | Q(customerid__isnull=True))
                        .values_list('document_id', flat=True)
                    )
                    return qs.filter(document_id__in=document_ids)
            else:
                # If user has no associated customer, return empty queryset 
                    return qs.none()
            
    
