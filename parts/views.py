
from django.db import transaction
from venv import create
from django.utils.safestring import mark_safe
from urllib.parse import urlencode

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.contrib import messages

from documents.models import TblDocumentLinks
from utils.generic_views import BulkUpdateView

from .models import (Tblpartslist,
                    Tblpartsprice,
                    SparepartView,
                    TblPartModel

)
from assets.models import Tblmodel


# import class based views
from django.views.generic import (UpdateView,
                                  CreateView,
                                  DeleteView,
                                  ListView,
                                  DetailView,
                                  FormView)



#import generic filter table view
from utils.generic_views import FilteredTableView

#import form tools
from .forms import (
    AddPartPrice,
    UpdatePartPrice,
    PartsBulkUpdateForm,
    CreatePartModelLinkForm
)

#import permission and login mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# Create your views here.
#part views
class PartsTableView(LoginRequiredMixin,PermissionRequiredMixin,
                  FilteredTableView):
    
    model = SparepartView
    paginate_by = 20
    permission_required = 'parts.view_tblpartslist'  
    template_name = "parts/parts_list.html"
    template_columns = {'open':'parts/tables/sparepart_open.html'}
    universal_search_fields = [
        'partid__icontains',
        'description__icontains',
        'part_number__icontains',
        'short_name__icontains',
        'supplier_name__icontains'
    ]


class PartDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                  DetailView):
    model = SparepartView
    template_name = "parts/part_view.html"
    fields = '__all__'
    permission_required = 'parts.view_tblpartslist'

class PartUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                  UpdateView):
    model = Tblpartslist
    fields = "__all__"
    template_name = "parts/partials/partial.html"
    permission_required = 'parts.change_tblpartslist'


    def get_success_url(self):
        return reverse("parts:part_detail", kwargs={'pk':self.object.partid})
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Part" 
        context["view_type"] = 'update'
        return context

class PartBulkUpdateView(BulkUpdateView):

    #filterset_class = PartFilter
    context_object_name = 'parts'
    model = SparepartView
    db_table = Tblpartslist
    permission_required = 'parts.change_tblpartslist'
    form_class = PartsBulkUpdateForm
    summary_field_names = ['supplier_name','inactive']
    success_url = reverse_lazy('parts:parts')


class PartDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                  DeleteView):
    model = Tblpartslist
    template_name = "parts/partials/partial.html"
    permission_required = 'assets.delete_tblbrands'
    success_url = reverse_lazy("parts:parts")
    permission_required = 'parts.delete_tblpartslist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Delete Part' 
        context['brand'] = Tblpartslist.objects.get(pk=self.kwargs.get('pk'))

        context["view_type"] = 'delete'
        return context

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            response = HttpResponse()
            response['HX-Redirect'] = self.get_success_url()
            return response
        
        except Exception as e:
            context = self.get_context_data(object=self.object)
            context['error_message'] = f"An error occurred while deleting the brand. Error Details: {str(e)}"
            return self.render_to_response(context)


class PartCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                  CreateView):
    model = Tblpartslist
    fields = "__all__"
    template_name = "parts/update_part.html"
    permission_required = 'parts.add_tblpartslist'

    def get_success_url(self):
        return reverse("parts:part_detail", kwargs={'pk':self.object.partid})
        
    def form_valid(self, form):
        try:           
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            context = self.get_context_data(object=self.object)

            if 'unique constraint' in str(e):  # your unique constraint name
                part_number = form['part_number'].value()
                supplier_id = form['supplier_id'].value()
                existing_part = Tblpartslist.objects.filter(part_number=part_number).filter(supplier_id=supplier_id)

                url = reverse('parts:part_detail', kwargs={'pk':existing_part[0].partid})
                messages.warning(self.request, mark_safe(f'This part number from the same supplier already exists - <a href="{url}">Go to Existing Part</a>'))
                return self.render_to_response(context)
            else:
                messages.warning(self.request, f"an error occurred")
                return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Create New Part' 
        context["view_type"] = 'create'
        return context


class SparePartPriceListView(LoginRequiredMixin, PermissionRequiredMixin,
                  ListView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices.html"
    context_object_name = "price_list"    
    permission_required = 'parts.view_tblpartsprice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["partid"] = self.request.GET.get('partid', None)
        return context
    

    def get_queryset(self, **kwargs):
        qs = super().get_queryset()
        partid = self.request.GET.get('partid', None)
        if partid:
            return super().get_queryset().filter(partid=partid)
        return qs

class SparePartPriceCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                  CreateView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices_create.html"
    form_class = AddPartPrice
    permission_required = 'parts.add_tblpartsprice'


    def get_success_url(self):
        return reverse('parts:part_prices_detail', kwargs={'pk':self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        partid = self.request.GET.get('partid', None)
        initial['partid'] = partid
        initial['effectivedate'] = now().date().isoformat()
        return initial
    
    def form_valid(self, form):
        try:           
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            context = self.get_context_data(object=self.object)
            context['error_message'] = f"An error occurred while adding price. Error Details: {str(e)}"
            return self.render_to_response(context)

class SparePartPriceDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                  DetailView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices.html#part_price"
    fields = '__all__'
    context_object_name = 'part_price'
    permission_required = 'parts.view_tblpartsprice'



class SparePartPriceDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                  DeleteView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices_delete.html"
    fields = '__all__'
    permission_required = 'parts.delete_tblpartsprice'


    def get_success_url(self):
        base_url = reverse('parts:part_prices')
        query_string = urlencode({'partid': self.object.partid.partid})
        return f"{base_url}?{query_string}"

    def post(self, request, *args, **kwargs):
        # Set self.object before the usual form processing flow.
        # Inlined because having DeletionMixin as the first base, for
        # get_success_url(), makes leveraging super() with ProcessFormView
        # overly complex.
        self.object = self.get_object()
        
        with transaction.atomic():
            TblDocumentLinks.delete_link_documents(self.object)
            self.object.delete()
        if request.htmx:
            return HttpResponse("")
        return HttpResponseRedirect(self.get_success_url())


class SparePartPriceUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                  UpdateView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices_update.html"
    form_class = UpdatePartPrice
    permission_required = 'parts.change_tblpartsprice'

    
    def get_success_url(self):
        return reverse('parts:part_prices_detail', kwargs={'pk':self.object.pk})
    
    def get_initial(self):
        initial = super().get_initial()
        initial['effectivedate'] =self.object.effectivedate.isoformat()
        return initial


#model link views

class PartLinkedModelListView(LoginRequiredMixin, PermissionRequiredMixin,
                  ListView):
    model = TblPartModel
    template_name = "parts/partials/linked_models.html"
    context_object_name = "linked_models"    
    permission_required = 'parts.view_tblpartmodel'


    def get_queryset(self, **kwargs):
        qs = super().get_queryset()
        partid = self.request.GET.get('partid', None)
        if partid:
            return super().get_queryset().filter(part=partid)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partid'] = self.request.GET.get('partid')
        return context


class LinkModelCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                  FormView):

    model = Tblmodel
    permission_required = 'parts.add_tblpartmodel'
    template_name = "parts/partials/linked_model_create.html"
    form_class = CreatePartModelLinkForm

    def get_success_url(self):
        return reverse('parts:part_detail', kwargs={'pk':self.partid})

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        partid = self.request.GET.get('partid')
        initial['partid'] = partid
        return initial

    def get_queryset(self):
        partid = self.request.GET.get('partid', None)
        qs =  super().get_queryset()
        linkedmodelids = TblPartModel.objects.filter(part=partid).values_list('model',flat=True)
        return qs.exclude(modelid__in=(linkedmodelids))    

    
    def form_valid(self,form):
        models = form.cleaned_data['models']
        self.partid = form.cleaned_data['partid']

        part = Tblpartslist.objects.get(partid=self.partid)

        existing  = set(TblPartModel.objects.filter(part=self.partid).values_list('model',flat=True))
        
        new = [TblPartModel(model=model,part=part) for model in models if model.pk not in existing]

        if new:
            with transaction.atomic():
                TblPartModel.objects.bulk_create(new)

        if self.request.htmx:
            response = HttpResponse("")
            url = reverse('parts:linked_models')
            query_params = urlencode({'partid':self.partid})
            
        
        return HttpResponseRedirect(self.get_success_url())


class LinkModelDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                  DeleteView):
    model = TblPartModel
    template_name = "parts/partials/linked_model_delete.html"
    permission_required = 'parts.delete_tblpartmodel'
    success_url = reverse_lazy("parts:linked_models")

    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        self.object.delete()
        if request.htmx:
            return HttpResponse("")
        return HttpResponseRedirect(self.success_url)

class LinkedModelDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                  DetailView):
    model = TblPartModel
    template_name = "parts/partials/linked_models.html#linked_model"
    fields = '__all__'
    context_object_name = "link"    
    permission_required = 'parts.view_tblpartmodel'


