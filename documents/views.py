from io import BytesIO
import io
from urllib.parse import urlencode
import uuid
from django.apps import apps
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, render
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, Http404
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.views import View
from PIL import Image
from django.core.exceptions import ValidationError
from assets.models import Tblassets, Tblmodel
from parts.models import Tblpartslist
# import models
from .models import (TblDocuments,
                     TblDocTableRef,
                     TblDocumentLinks,
                     DocumentsView,
                     TemporaryUpload,
                     )

# import generic views
from django.views.generic import (
    CreateView, UpdateView,
    DeleteView, ListView,
    DetailView, FormView,
    TemplateView
)

# import forms
from .forms import (
    DocumentLinkCreateForm,
    DocumentUpdateForm,
    TempFileUploadForm,
    QuickScannerForm,
    LinkTemporaryDocumentForm
)

# import generic filter table view
from utils.generic_views import FilteredTableView
from django.db.models import ForeignKey, Q


# import mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .mixins import DocumentPermissionMixin
from pdf2image import convert_from_path
from .utils import clear_extraction_results, quick_scan_barcode, save_extraction_results
from .utils import get_extraction_results


# Create your views here.


class DocumentAndLinkCreateView(
    LoginRequiredMixin,
    DocumentPermissionMixin,
    CreateView

):
    model = TblDocuments
    form_class = DocumentLinkCreateForm
    template_name = "documents/partials/document_crud_modal.html"

    success_url = reverse_lazy('documents:table_document_links')  # or wherever you want

    permission_required = 'documents.add_tbldocuments'

    def get_initial(self):
        # Pre-fill initial data for the form if needed
        initial = super().get_initial()
        initial['link_row'] = self.request.GET.get('link_row')
        initial['link_table'] = self.request.GET.get('link_table')  # Extract model name
        return initial

    def form_valid(self, form):
        try:
            # Create the related DocumentLink
            link_row = form.cleaned_data.get('link_row')
            link_table_name = form.cleaned_data.get('link_table')
            table_id = TblDocTableRef.objects.get(table_name=link_table_name)
            document_type_id = form.cleaned_data.get('document_type_id')
            # check whether a new file is being uploaded or permanent document
            # is being created from temporary uploads
            uploaded_file = self.request.FILES['document_bytea']
            document_name = form.cleaned_data.get('document_name')
            document_description = form.cleaned_data.get('document_description')

            TblDocuments.from_file(
                document_name=document_name,
                document_description=document_description,
                content=uploaded_file.read(),
                mime_type=uploaded_file.content_type,
                file_size=uploaded_file.size,
                document_type_id=document_type_id,
                link_table_id=table_id,
                link_row=link_row,
            )

            if self.request.htmx:
                return HttpResponse(status=204)
            else:
                return HttpResponseRedirect(self.success_url)

        except Exception as e:
            if 'unique_has' in str(e):
                import hashlib
                uploaded_file.seek(0)
                dup_hash = hashlib.sha256(uploaded_file.read()).hexdigest()
                existing_doc = TblDocuments.objects.filter(document_hash=dup_hash).first()
                messages.warning(self.request, f"Document already exists in Database.Existing document id: {existing_doc.pk}")
            else:
                messages.warning(self.request, f"Error:{str(e)}")
            return self.form_invalid(form)


class DocumentLinkDeleteView(
    LoginRequiredMixin,
    DocumentPermissionMixin,
    DeleteView
):
    model = DocumentsView
    template_name = "documents/partials/document_crud_modal.html"
    permission_required = 'documents.delete_tbldocuments'

    success_url = reverse_lazy('documents:list_documents')  # or wherever you want

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        link = TblDocumentLinks.objects.get(document_link_id=self.object.document_link_id)
        link.delete()
        try:
            document = TblDocuments.objects.get(document_id=self.object.document_id)
            document.delete()
        except Exception as e:
            messages.warning(self.request, f"Link Deleted. But document is still linked to other records. Error:{str(e)}")
            return HttpResponseRedirect(success_url)



        if self.request.htmx:
                # Return an empty 204 response so HTMX knows it's successful
                return HttpResponse(status=204)
        return HttpResponseRedirect(success_url)



class DocumentLinkUpdateView(
    LoginRequiredMixin,
    DocumentPermissionMixin,
    UpdateView
):
    model = DocumentsView
    template_name = "documents/partials/document_crud_modal.html"
    fields = '__all__'
    permission_required = 'documents.change_tbldocuments'
    success_url = reverse_lazy('documents:table_document_links')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # update document link
                link = TblDocumentLinks.objects.get(document_link_id=self.object.document_link_id)
                link.link_table = form.cleaned_data['link_table']
                link.link_row = form.cleaned_data['link_row']
                link.save()
                # update document
                document = TblDocuments.objects.get(document_id=self.object.document_id)
                document.document_name = form.cleaned_data['document_name']
                document.document_description = form.cleaned_data['document_description']
                document.document_type_id = form.cleaned_data['document_type_id']
                document.save()

                if self.request.htmx:
                    return HttpResponse(status=204)
                return redirect(self.get_success_url())

        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context['error_message'] = f"An error occurred while updating the document. Error Details: {str(e)}"
            return self.render_to_response(context)

    def form_invalid(self, form):
        # Handle invalid form submission
        context = self.get_context_data(form=form)
        context['error_message'] = "The form contains invalid data. Please correct the errors and try again."
        return self.render_to_response(context)

class DocumentUpdateView(LoginRequiredMixin,
                         DocumentPermissionMixin,
                         UpdateView):
    model = TblDocuments
    template_name = 'documents/document_update.html'
    permission_required =   'documents.change_tbldocuments'
    form_class = DocumentUpdateForm
    success_url = reverse_lazy('documents:table_document_links')

    def form_valid(self, form):
        uploaded_file = self.request.FILES.get('document_bytea')
        if uploaded_file:
            form.instance.document_bytea = uploaded_file.read()
            form.instance.mime_type = uploaded_file.content_type
            form.instance.file_size = uploaded_file.size
        return  super().form_valid(form)
        

class DocumentLinksTableView(LoginRequiredMixin,
                                DocumentPermissionMixin,
                                FilteredTableView):
    model = DocumentsView
    paginate_by = 20
    permission_required = 'documents.view_documentsview'
    template_name = "documents/documents_links.html"
    template_columns= {'actions':"documents/tables/document_links_buttons.html"}
    universal_search_fields =[
            'document_name__icontains',
            'document_description__icontains',
            'document_id__icontains',
    ]
    exclude = ['document_bytea']


class DocumentsTableView(LoginRequiredMixin,
                                DocumentPermissionMixin,
                                FilteredTableView):
    model = TblDocuments
    paginate_by = 20
    permission_required = 'documents.view_documentsview'
    template_name = "documents/documents.html"
    template_columns= {'actions':"documents/tables/documents_buttons.html"}
    universal_search_fields =[
            'document_name__icontains',
            'document_description__icontains',
            'document_id__icontains',
    ]
    exclude = ('document_bytea',)


class DocumentDownloadView(LoginRequiredMixin,
                           DocumentPermissionMixin,
                           DetailView):
    model = DocumentsView

    permission_required = 'documents.view_tbldocuments'


    def render_to_response(self,context,**response_kwargs):
        document_id = self.get_object().document_id
        document = TblDocuments.objects.get(document_id=document_id)
        
        return HttpResponse(
            document.document_bytea,
            content_type=document.mime_type,
            headers={
                'Content-Disposition': f'attachment; filename="{document.document_name}"'
            }
        )

def get_document_links_for_object(object,possible_links):
    qfilters  = Q()
    model = object.__class__
    for field in model._meta.get_fields():
        if isinstance(field,ForeignKey):
            related_model = field.remote_field.model
            related_model_name = related_model.__name__.lower()
            if related_model_name in possible_links:
                table = TblDocTableRef.objects.filter(table_name__iexact=related_model_name).first()
                pk = getattr(object, str(field.name)).pk
                if table:
                    qfilters |= (Q(link_table = table) & Q(link_row = pk))|get_document_links_for_object(getattr(object, str(field.name)),possible_links)
    return qfilters
                    

class DocumentListView(LoginRequiredMixin,
                       DocumentPermissionMixin,
                       ListView):
    model=DocumentsView
    template_name='documents/partials/document_list.html'
    context_object_name = "documents"
    permission_required = 'documents.view_documentsview'


    def get_queryset(self):
        # Filter jobs by assetid passed in the URL
        link_row = self.request.GET.get('link_row')
        app_model = self.request.GET.get('app_model')
        link_table = self.request.GET.get('link_table')

        app_name,model_name = app_model.split('.')
        table_id = TblDocTableRef.objects.get(table_name__iexact=link_table)

        document_link_filters = Q()

        document_link_filters |=  (
            Q(link_table=table_id) &
            Q(link_row=link_row)
        )
        #get main model and object  
        model = apps.all_models[app_name][model_name.lower()]
        object = model.objects.get(pk=link_row)

        possible_links = [name.lower() for name in TblDocTableRef.objects.values_list('table_name',flat=True)]
        
        document_link_filters |= get_document_links_for_object(object,possible_links)

        
        if not self.request.user.is_staff:
            document_link_filters &= Q(customerid=self.request.user.customerid) | Q(customerid__isnull=True)
        return DocumentsView.objects.filter(document_link_filters)
    
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            documents = self.get_queryset()
            grouped_documents = {}

            from itertools import groupby
            from operator import attrgetter

            for key, group in groupby(documents, key=attrgetter('document_type_id')):
                grouped_documents[key] = list(group)
            context['grouped_documents'] = grouped_documents
            return context


def resizeimg(img):

    # Calculate new size (50%)
    new_width = img.width // 2
    new_height = img.height // 2

    # Resize
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return resized_img

class SaveTempFiles:
    def __init__(self, temp_files, link_row, link_table,document_type=None,file_name=None):
        self.temp_files_list = temp_files
        self.link_row = link_row
        self.table_id = TblDocTableRef.objects.get(table_name=link_table)
        self.file_name = file_name
        self.document_type = document_type
    
    def save_single_file(self):
        file = self.temp_files_list[0]
        with open(file.file.path, 'rb') as f:
            content = f.read()
        TblDocuments.from_file(
            temp_file=file,
            content=content,
            document_type_id=self.document_type,
            link_table_id=self.table_id,
            link_row=self.link_row,
        )



    def save_all(self):
        """
        Save all files permanently and link them to the row/table.
        """
        with transaction.atomic():
            if len(self.temp_files_list) == 1:
                self.save_single_file()

            else:
                image_files = [file for file in self.temp_files_list if 'image/' in file.mime_type]
                #Open all images
                if image_files:
                    images = [Image.open(img.file.path).convert("RGB") for img in image_files]
                    downscaled_images = list(map(resizeimg,images))
                    
                    # Create a bytes buffer instead of saving to disk
                    pdf_bytes_io = io.BytesIO()
                    # Save as PDF
                    # The first image is used as the starting point, the rest are appended
                    downscaled_images[0].save(
                        pdf_bytes_io,
                        format='PDF',
                        save_all=True,
                        append_images=downscaled_images[1:]
                    )
                    # Get bytes for storage
                    pdf_bytes = pdf_bytes_io.getvalue()
                    pdf_bytes_io.close()



                    document = TblDocuments.from_file(
                        document_name=f"{uuid.uuid4()}"+'.pdf',
                        mime_type='application/pdf',
                        content=pdf_bytes,
                        file_size=len(pdf_bytes),
                        document_type_id=self.document_type,
                        link_table_id=self.table_id,
                        link_row=self.link_row
                    )

                    for image in image_files:
                        image.delete()

class DocumentPreView(LoginRequiredMixin,
                      View):

    def get(self, request):
        pk = request.GET.get('pk')
        user = request.user        
        try:
            temp_upload = TemporaryUpload.objects.get(pk=pk,user=user)
        except TemporaryUpload.DoesNotExist:
            raise Http404("File not found or is not yours")
        mime_type = temp_upload.mime_type
        if mime_type == 'application/pdf':  
            page = convert_from_path(temp_upload.file.path,first_page=1,last_page=1)
            image = page[0]
            buffer = BytesIO()
            image.save(buffer,format='PNG')
            buffer.seek(0)

            return FileResponse(buffer,content_type="image/png")    
        return FileResponse(temp_upload.file.open('rb'),content_type=mime_type)

class TempFilesDeleteAllView(LoginRequiredMixin,
                          DeleteView):    
    success_url = reverse_lazy('documents:user_temp_files')

    def post(self,request,*args, **kwargs):
        user = request.user
        files = TemporaryUpload.objects.filter(user=user)
        for f in files:
            f.delete()      
        
        return HttpResponseRedirect(self.success_url)
    
class TempFilesDeleteView(LoginRequiredMixin,
                          DeleteView):    
    model = TemporaryUpload
    success_url = reverse_lazy('documents:user_temp_files')
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user == self.object.user:
            self.object.delete()
      

        # HTMX request → empty response
        if request.htmx:
            response = HttpResponse(status=200)

            if not TemporaryUpload.objects.filter(group=self.object.group,user=request.user).exists():
                response['HX-Retarget'] = f'#group_{self.object.group}'
                
            return response # No Content

        return HttpResponseRedirect(self.success_url)
        

class TemporaryUploadCreateView(LoginRequiredMixin,
                                PermissionRequiredMixin,
                                CreateView):
    model = TemporaryUpload
    template_name = "documents/partials/temp_document_create.html"
    form_class = TempFileUploadForm
    permission_required = 'documents.add_tbl_temporaryupload'

    
    def form_valid(self, form):
        file = self.request.FILES.get('files')
        raw_group = self.request.POST.get('group')

        groups = list(TemporaryUpload.objects.filter(user=self.request.user).values_list('group',flat=True))

        if groups:
            latest_group = max(groups)
        else:
            latest_group = 0
        #cases when group is 'new' or a group is specified. otherwise the latest group will be used.
        if raw_group:
            try:
                group = int(raw_group)
                group_content_type = TemporaryUpload.objects.filter(group=group).first().mime_type
                if 'image' not in group_content_type or 'image' not in file.content_type:
                    return self.form_invalid(form)

            except:   
                if 'new' in raw_group:
                    group = latest_group+1

        else:
            group = latest_group
        
        object = TemporaryUpload.from_uploaded_file(
            user = self.request.user,
            file = file,
            group = group,
        )



        if self.request.htmx:
            group_document_count = TemporaryUpload.objects.filter(user=self.request.user, group=object.group).count()
            if group_document_count == 1:
                context = {'group':object.group,'temp_files':[object]}
                return render(self.request,'documents/partials/temp_file_group.html',context=context)
            else:
                context = {'file':object}
                return render(self.request, 'documents/partials/temp_file.html', context)
            
        
        else:
            return HttpResponseRedirect(reverse('documents:create_temp_files'))
    
    def form_invalid(self, form):
            messages.warning(self.request, 'Incorrect file type uploaded.')
            response = render(self.request, "partials/messages.html")
            response['HX-Retarget'] = "this"
            response['HX-Reswap'] = "beforeend"
            return response


class TempUploadDetailView(LoginRequiredMixin,
                           PermissionRequiredMixin,
                           DetailView):
    model = TemporaryUpload
    template_name = 'documents/partials/temp_file.html'
    context_object_name = 'file'
    permission_required = 'documents.view_tbl_temporaryupload'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise Http404("File not found or is not yours")
        return obj
    

class TempUploadListView(LoginRequiredMixin,
                         ListView):
    model = TemporaryUpload
    template_name = 'documents/temp_files_list.html'
    context_object_name = "temp_files_groups"
    permission_required = 'documents.view_tbl_temporaryupload'


    def get_queryset(self):
        qs = super().get_queryset()

        group = self.request.GET.get('group')
        if group:
            user_qs = qs.filter(user=self.request.user,group=group)

        else:
            user_qs = qs.filter(user=self.request.user)
        if user_qs:
            grouped_qs = {}
            for obj in user_qs:
                key = getattr(obj,'group')
                if key not in grouped_qs:
                    grouped_qs[key] = []
                grouped_qs[key].append(obj)
                sorted_grouped_qs = dict(sorted(grouped_qs.items()))
            return sorted_grouped_qs

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['success_url'] = self.request.GET.get('success_url')
        context['target'] = self.request.GET.get('target')
        return context


class LinkTemporaryDocumentView(TempUploadListView,
                                PermissionRequiredMixin,
                                FormMixin):
    model = TemporaryUpload
    form_class = LinkTemporaryDocumentForm
    success_url = reverse_lazy('documents:table_document_links')  # or wherever you want
    permission_required = 'documents.add_tbldocuments'
    template_name = 'documents/partials/temp_upload_group_select.html'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        group = self.request.POST.get('group')
        link_row = self.request.POST.get('link_row')
        link_table_name = self.request.POST.get('link_table')
        
        # Create the related DocumentLink

        document_type = form.cleaned_data.get('document_type')

        files = TemporaryUpload.objects.filter(
            group=group,
            user=self.request.user
        )
        temp_documents = SaveTempFiles(
            files,
            link_row=link_row,
            link_table=link_table_name,
            document_type=document_type,
        )
        temp_documents.save_all()

        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        messages.warning(self.request, 'Failed to link files.')
        return render(self.request, self.template_name, context={})


class QuickScanner(
    LoginRequiredMixin,
    FormView
):
    form_class = QuickScannerForm
    template_name = 'documents/quick_scanner.html'

    def form_valid(self, form):
        file = self.request.FILES.get('file')
        scanned_code = form.cleaned_data['scanned_code']
        result=None

        from .services.gs1_parser import parse_gs1code, gs1_resolver, non_gs1_result
        try:
            decoded_info = parse_gs1code(file=file, scanned_code=scanned_code)
            result = gs1_resolver(decoded_info)

        except ValidationError as e:
            if hasattr(e, "message_dict"):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                messages.warning(
                    self.request, str(e)
                )
                form.add_error(None, e.message)

        if result is None:
            result = non_gs1_result(scanned_code)
            non_staff_search_term = scanned_code
        else:
            non_staff_search_term = f"{result.get('SERIAL', '')} {result.get('ASSET_NO', '')}"

        if self.request.user.is_staff:
            return self.render_to_response(self.get_context_data(form=form, result=result))
        else:
            base_url = reverse('assets:assets_list')
            qp = urlencode({'universal_search': non_staff_search_term})
            return HttpResponseRedirect(f"{base_url}?{qp}")

    def form_invalid(self, form):
        return render(self.request, self.template_name, context={'form': form})

    def get_context_data(self, result=None, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['result'] = result
        return ctx


URL_MAP = {
    'device_id':'assets:barcode_output',
    'service_report':'jobs:report_reader_output',
    'invoice':'procurement:invoices_reader_output',
    'delivery_note':'procurement:delivery_note_reader_output',
}

class GetExtractedData(LoginRequiredMixin,TemplateView):
    template_name = 'documents/partials/get_extracted_data.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.kwargs.get('group')
        if group:
            extracted_data = get_extraction_results(self.request.user,group)
            context["extracted_data"] = extracted_data 
            context["group"] = group
            if extracted_data:
                document_type = extracted_data.get('document_type',None)
                if document_type:
                    context['action'] = reverse(URL_MAP.get(document_type),kwargs={'temp_file_group':group})
             

        return context


class UpdateExtractedData(LoginRequiredMixin,TemplateView):
    template_name = 'documents/update_extracted_data.html'

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.kwargs.get('temp_file_group')
        if group:
            extracted_data = get_extraction_results(self.request.user,group)
            context["extracted_data"] = extracted_data 
            context["group"] = group
        return context
    
    def post(self, request, *args, **kwargs):
        form = request.POST.dict()

        if 'device_id' in form.get('document_type'):
            form['suggested_brands'] = request.POST.getlist('suggested_brands')
            form['suggested_categories'] = request.POST.getlist('suggested_categories')

        group = self.kwargs.get('temp_file_group')
        form.pop('csrfmiddlewaretoken')
        save_extraction_results(
            user_id = self.request.user,
            group = group,
            results = form,
            hours = 1
        )

        query_params = urlencode({'group':group})

        URL_MAP = {
            'device_id':'assets:barcode_output',
            'service_report':'jobs:report_reader_output',
            'invoice':'procurement:invoices_reader_output',
            'delivery_note':'procurement:delivery_note_reader_output',
        }

        document_type = form.get('document_type')

        if document_type not in URL_MAP:
            raise ValueError(f"Unknown document type: {document_type}")

        url = reverse(URL_MAP.get(document_type),kwargs={'temp_file_group':group})
        
        return HttpResponseRedirect(url)

class ExtractedDateDeleteView(LoginRequiredMixin,View):
    def get_success_url(self):
        # Use self.object to access the updated object
        return reverse('documents:get_extracted_data', kwargs={'group': self.group})

    def post(self, request, *args, **kwargs):
        self.group = self.kwargs.get('group')
        user = request.user
        clear_extraction_results(user,self.group)
        return HttpResponseRedirect(self.get_success_url())



