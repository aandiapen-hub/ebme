from io import BytesIO
import json
from django.apps import apps
from django.views.generic.edit import FormMixin
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from .services.documents import (
    create_document_from_file,
    save_temp_files,
    delete_document_link,
    save_temp_document,
)
from documents.services.document_parser import (
    temp_group_resolver,
)

from documents.services.process_document import extract_information_from_temp_group
from documents.services.context.registry import build_document_context
from django.tasks import default_task_backend
from urllib.parse import urlencode

# import models
from .models import (
    TblDocuments,
    TblDocumentLinks,
    TempUploadGroup,
    TemporaryUpload,
)



# import generic views
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    DetailView,
    FormView,
)

# import forms
from .forms import (
    DocumentCreateForm,
    DocumentUpdateForm,
    TempFileUploadForm,
    LinkTemporaryDocumentForm,
    DocumentLinkUpdateForm,
    BulkLinkDocument,
    EmptyForm,
    TempUploadGroupUpdateForm,
    AssetDataUpdate
)

# import generic filter table view
from utils.generic_views import FilteredTableView, BulkUpdateView
from django.db.models import ForeignKey


# import mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .mixins import DocumentLinkPermissionMixin
from pdf2image import convert_from_path

# Create your views here.
DOCUMENT_LINK_SEARCH = [
    "documentid__document_name__icontains",
    "documentid__icontains",
]


class DocumentAndLinkCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = TblDocuments
    form_class = DocumentCreateForm
    template_name = "documents/partials/document_crud_modal.html"

    success_url = reverse_lazy("documents:table_document_links")  # or wherever you want

    permission_required = "documents.add_tbldocuments"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        object_id = self.request.GET.get("object_id")
        content_type = self.request.GET.get("content_type")
        model = apps.get_model(content_type)
        context["object"] = model.objects.get(pk=object_id)
        context["content_type"] = content_type
        return context

    def form_valid(self, form):
        # Create the related DocumentLink
        object_id = self.request.GET.get("object_id")
        content_type = self.request.GET.get("content_type")
        model = apps.get_model(content_type)
        object = model.objects.get(pk=object_id)

        document_type_id = form.cleaned_data.get("document_type_id")
        # check whether a new file is being uploaded or permanent document
        # is being created from temporary uploads
        uploaded_file = self.request.FILES["document_bytea"]
        document_name = form.cleaned_data.get("document_name")
        document_description = form.cleaned_data.get("document_description")

        create_document_from_file(
            uploaded_file=uploaded_file,
            document_type_id=document_type_id,
            document_name=document_name,
            content_object=object,
            document_description=document_description,
        )

        if self.request.htmx:
            return HttpResponse(status=204)
        else:
            return HttpResponseRedirect(self.success_url)


class DocumentLinkDeleteView(
    LoginRequiredMixin, DocumentLinkPermissionMixin, DeleteView
):
    model = TblDocumentLinks
    template_name = "documents/partials/document_link_delete_view.html"
    permission_required = "documents.delete_tbldocumentlinks"

    success_url = reverse_lazy("documents:table_document_links")  # or wherever you want

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        delete_document_link(self.object)
        if self.request.htmx:
            # Return an empty 204 response so HTMX knows it's successful
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "documentUpdated"
            return response
        return HttpResponseRedirect(self.success_url)


class DocumentLinkUpdateView(
    LoginRequiredMixin, DocumentLinkPermissionMixin, UpdateView
):
    model = TblDocumentLinks
    template_name = "documents/partials/document_crud_modal.html"
    form_class = DocumentLinkUpdateForm
    permission_required = "documents.change_tbldocumentlinks"
    success_url = reverse_lazy("documents:table_document_links")

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "documentUpdated"
            return response
        return redirect(self.get_success_url())


class DocumentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblDocuments
    template_name = "documents/document_detail_view.html"
    permission_required = "documents.view_tbldocuments"
    context_object_name = "document"


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TblDocuments
    template_name = "documents/document_update.html"
    permission_required = "documents.change_tbldocuments"
    form_class = DocumentUpdateForm

    def get_success_url(self):
        return reverse("documents:view_document", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        document = self.get_object()
        document_type_id = form.cleaned_data.get("document_type_id")
        # check whether a new file is being uploaded or permanent document
        # is being created from temporary uploads
        uploaded_file = self.request.FILES.get("document_bytea", None)
        document_name = form.cleaned_data.get("document_name")
        document_description = form.cleaned_data.get("document_description")

        try:
            create_document_from_file(
                document=document,
                uploaded_file=uploaded_file,
                document_type_id=document_type_id,
                document_name=document_name,
                document_description=document_description,
            )
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

        if self.request.htmx:
            return HttpResponse(status=204)
        else:
            return HttpResponseRedirect(self.get_success_url())


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TblDocuments
    template_name = "documents/document_update.html"
    permission_required = "documents.delete_tbldocuments"
    success_url = reverse_lazy("documents:table_documents")


class DocumentLinksTableView(
    LoginRequiredMixin, DocumentLinkPermissionMixin, FilteredTableView
):
    model = TblDocumentLinks
    paginate_by = 20
    permission_required = "documents.view_tbldocumentlinks"
    template_name = "documents/documents_links.html"
    template_columns = {"actions": "documents/tables/document_links_buttons.html"}
    universal_search_fields = DOCUMENT_LINK_SEARCH
    exclude = ["document_bytea"]

    bulk_actions = {
        "bulk_delete": {
            "url": reverse_lazy("documents:bulk_delete_links"),
            "permission": "documents.bulk_delete_links",
            "name": "Delete",
        },
    }


class DocumentsTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = TblDocuments
    paginate_by = 20
    permission_required = "documents.view_tbldocuments"
    template_name = "documents/documents.html"
    template_columns = {"open": "documents/tables/open.html"}
    universal_search_fields = [
        "document_name__icontains",
        "document_description__icontains",
        "document_id__icontains",
    ]
    exclude = ("document_bytea",)


class DocumentDownloadFromLinkView(
    LoginRequiredMixin, DocumentLinkPermissionMixin, DetailView
):
    model = TblDocumentLinks
    permission_required = "documents.view_tbldocumentlinks"

    def render_to_response(self, context, **response_kwargs):
        document_link = self.get_object()
        return HttpResponse(
            document_link.documentid.document_bytea,
            content_type=document_link.documentid.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document_link.documentid.document_name}"'
            },
        )


class DocumentDownloadView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblDocuments
    permission_required = "documents.view_tbldocuments"

    def render_to_response(self, context, **response_kwargs):
        document = self.get_object()
        return HttpResponse(
            document.document_bytea,
            content_type=document.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.document_name}"'
            },
        )


def get_document_links_for_object(object):
    related_links = TblDocumentLinks.objects.none()

    if hasattr(object, "document_links"):
        related_links |= object.document_links.all()
    model = object.__class__
    for field in model._meta.get_fields():
        if isinstance(field, ForeignKey):
            related_object = getattr(object, str(field.name))
            if hasattr(related_object, "document_links"):
                related_links |= (
                    related_object.document_links.all()
                    | get_document_links_for_object(getattr(object, str(field.name)))
                )
    return related_links


class DocumentListView(LoginRequiredMixin, DocumentLinkPermissionMixin, ListView):
    model = TblDocumentLinks
    template_name = "documents/partials/document_list.html"
    context_object_name = "documents"
    permission_required = "documents.view_tbldocumentlinks"

    def get_queryset(self):
        # Filter jobs by assetid passed in the URL
        qs = super().get_queryset()
        object_id = self.request.GET.get("object_id")
        content_type = self.request.GET.get("content_type")
        model = apps.get_model(content_type)
        object = model.objects.get(pk=object_id)

        document_links = get_document_links_for_object(object)

        return qs.filter(pk__in=document_links.values_list("pk", flat=True)).order_by(
            "documentid__document_type_id"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        documents = self.get_queryset()
        if documents is not None:
            grouped_documents = {}
            from itertools import groupby

            for key, group in groupby(
                documents, key=lambda d: d.documentid.get_document_type_id_display()
            ):
                grouped_documents[key] = list(group)
            context["grouped_documents"] = grouped_documents
        return context


class DocumentPreView(LoginRequiredMixin, DetailView):
    model = TemporaryUpload

    def get(self, request, *args, **kwargs):
        temp_upload = self.get_object()
        mime_type = temp_upload.mime_type
        if mime_type in [None, '']:
            return HttpResponse(status=200)

        if mime_type == "application/pdf":
            page = convert_from_path(temp_upload.file.path, first_page=1, last_page=1)
            image = page[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            return FileResponse(buffer, content_type="image/png")
        return FileResponse(temp_upload.file.open("rb"), content_type='image/jpeg')


class TempFilesDeleteAllView(LoginRequiredMixin, FormView):
    success_url = reverse_lazy("documents:user_temp_files")
    form_class = EmptyForm

    def get_groups(self):
        return TempUploadGroup.objects.filter(user=self.request.user)

    def form_valid(self, form):
        self.get_groups().delete()
        return super().form_valid(form)



class TempFilesDeleteView(LoginRequiredMixin, DeleteView):
    model = TemporaryUpload
    success_url = reverse_lazy("documents:user_temp_files")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user == self.object.group.user:
            self.object.delete()

        # HTMX request → empty response
        if request.htmx:
            response = HttpResponse(status=200)

            if not TemporaryUpload.objects.filter(
                group=self.object.group
            ).exists():
                response["HX-Retarget"] = f"#group_{self.object.group.pk}"

            return response  # No Content

        return HttpResponseRedirect(self.success_url)


class ExtractTextFromImages(LoginRequiredMixin, FormView):
    form_class = EmptyForm

    def get_success_url(self):
        return reverse('documents:temp_group', kwargs={'pk': self.kwargs.get('pk')})

    def form_valid(self, form):
        task = extract_information_from_temp_group.enqueue(group_id=str(self.kwargs.get('pk')))

        group = TempUploadGroup.objects.get(pk=self.kwargs.get('pk'))
        group.task_result_id = str(task.id)
        group.save()

        response = HttpResponse()
        response['HX-Redirect'] = self.get_success_url() 
        return response


class GetTaskResult(LoginRequiredMixin, DetailView):
    model = TempUploadGroup
    context_object_name = 'group'
    permission_required = "documents.view_tbl_tempuploadgroup"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.htmx and self.object.task_result_id:
            task_result = default_task_backend.get_result(
                self.object.task_result_id
            )
            if task_result.status not in ['SUCCESSFUL', 'FAILED']:
                response = HttpResponse(status=200)
                return response

        context = self.get_context_data(object=self.object)

        if self.object.task_result_id:
            context['task_result'] = task_result
        response = self.render_to_response(context)
        response['HX-Reswap'] = 'outerHTML'
        response['HX-Trigger'] = json.dumps({'data_resolved': True})

        return response

    def get_template_names(self):
        return ['documents/partials/task_progress.html']


class TemporaryUploadCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "documents/temp_file_group.html#form"
    form_class = TempFileUploadForm
    permission_required = "documents.add_tbl_temporaryupload"

    def get_success_url(self):
        return reverse("documents:temp_group", kwargs={'pk': self.object.group})

    def form_valid(self, form):
        file = self.request.FILES.get("files")
        group_id = self.request.GET.get("group", None)
        scanned_code = self.request.POST.get("scanned_code", None)

        if group_id in ['new', 'quick']:
            group_id = None

        try:
            self.object = save_temp_document(
                user=self.request.user,
                group_id=group_id,
                file=file,
                scanned_code=scanned_code,
            )
        except ValidationError as e:
            form.add_error(None, str(e.message_dict['__all__'][0]))
            return self.form_invalid(form, str(e.message_dict['__all__']))

        if self.request.htmx:
            group_document_count = TemporaryUpload.objects.filter(
                group=self.object.group
            ).count()
            if group_document_count == 1:
                context = {"group": self.object.group, "temp_files": [self.object]}
                response = render(
                    self.request,
                    "documents/temp_file_group.html#temp_group",
                    context=context,
                )
                response['HX-Retarget'] = '#images_div'
                return response
            else:
                context = {"file": self.object}
                return render(
                    self.request, "documents/partials/temp_file.html", context
                )

        else:
            return super().form_valid(form)

    def form_invalid(self, form):
        group = TempUploadGroup.objects.get(pk=self.request.GET.get("group"))
        response = self.render_to_response(self.get_context_data(form=form, group=group))
        response["HX-Reswap"] = "outerHTML"
        response['HX-Retarget'] = 'this'
        return response


class TempUploadGroupView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TempUploadGroup
    context_object_name = "group"
    permission_required = "documents.view_tbl_temporaryupload"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_template_names(self):
        return ["documents/temp_file_group.html"]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(**build_document_context(user=self.request.user, temp_group=self.object))
        return context


class TempUploadGroupUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TempUploadGroup
    permission_required = "documents.change_tbl_temporaryupload"
    form_class = TempUploadGroupUpdateForm
    template_name = 'documents/temp_file_group_update.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse('documents:temp_group', kwargs={'pk':self.object.pk})


class TempUploadMergedDataUpdate(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = "documents.change_tbl_temporaryupload"
    form_class = AssetDataUpdate
    template_name = 'documents/temp_group_data_update.html'

    def get_success_url(self):
        group_pk = self.kwargs.get('pk')
        return reverse('documents:temp_group', kwargs={'pk': group_pk})

    def get_initial(self):
        initial = super().get_initial()
        group_pk = self.kwargs.get('pk')
        group = TempUploadGroup.objects.get(pk=group_pk)
        data = group.extracted_json.get('merged_gs1_ai')
        for key, value in data.items():
            initial[key] = value
        return initial

    def form_valid(self, form):
        group_pk = self.kwargs.get('pk')
        group = TempUploadGroup.objects.get(pk=group_pk)
        data = group.extracted_json.get('merged_gs1_ai')
        for key, value in form.cleaned_data.items():
            if isinstance(value, QuerySet):
                data[key] = list(value.values_list("pk", flat=True))
            else:
                data[key] = value
        group.save(update_fields=['extracted_json'])
        temp_group_resolver(group.pk)
        return super().form_valid(form)

class TempUploadGroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TempUploadGroup
    permission_required = "documents.add_tbl_temporaryupload"
    template_name = 'documents/temp_group_delete.html'
    success_url = reverse_lazy('documents:user_temp_files')


class TempUploadListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TempUploadGroup
    template_name = "documents/temp_group_list.html"
    context_object_name = "temp_groups"
    permission_required = "documents.view_tbl_temporaryupload"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["success_url"] = self.request.GET.get("success_url")
        context["target"] = self.request.GET.get("target")
        return context


class LinkTemporaryDocumentView(TempUploadListView, PermissionRequiredMixin, FormMixin):
    model = TemporaryUpload
    form_class = LinkTemporaryDocumentForm
    success_url = reverse_lazy("documents:table_document_links")  # or wherever you want
    permission_required = "documents.add_tbldocuments"
    template_name = "documents/partials/temp_upload_group_select.html"

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        group = self.request.POST.get("group")

        object_id = self.request.GET.get("object_id")
        content_type = self.request.GET.get("content_type")

        model = apps.get_model(content_type)
        object = model.objects.get(pk=object_id)

        # Create the related DocumentLink

        document_type = form.cleaned_data.get("document_type")

        save_temp_files(
            group=group,
            user=self.request.user,
            content_object=object,
            document_type=document_type,
        )

        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        messages.warning(self.request, "Failed to link files.")
        return render(self.request, self.template_name, context={})


class QuickScanner(LoginRequiredMixin, FormView):
    form_class = TempFileUploadForm
    template_name = "documents/quick_scanner.html"
    temp_group = None

    def form_valid(self, form):
        file = self.request.FILES.get("files")
        scanned_code = self.request.POST.get("scanned_code", None)
        try:
            self.object = save_temp_document(
                user=self.request.user,
                file=file,
                scanned_code=scanned_code
            )

        except ValidationError as e:
            if e.message_dict['search']:
                # when a non gs1 code is quick searched
                self.object = e.message_dict['search'][0]

        response = HttpResponseRedirect(self.get_success_url())
        return response

    def get_success_url(self):
        if isinstance(self.object, TemporaryUpload):
            return reverse('documents:temp_group', kwargs={'pk': self.object.group.pk})
        else:
            url = reverse('assets:assets_list')
            query_params = urlencode({
                'universal_search': self.object
            })
            return f"{url}?{query_params}"

    def form_invalid(self, form):
        return render(self.request, self.template_name, context={"form": form})


class BulkLinkDocument(BulkUpdateView):
    permission_required = "documents.bulk_create_links"
    model = None  # defined in url
    template_name = "documents/partials/bulk_create_document_links.html"  # override in subclass - Mandatory
    universal_search_fields = None  # defined in url
    success_view = None  # defined in url
    operation = "create_link"
    table_to_update = TblDocumentLinks

    form_class = BulkLinkDocument
    link_source_field = "documentid"
    link_target_field = "content_object"


class BulkDeleteLink(BulkUpdateView):
    permission_required = "documents.bulk_delete_links"
    model = TblDocumentLinks
    template_name = "documents/partials/bulk_delete_document_links.html"  # override in subclass - Mandatory
    universal_search_fields = DOCUMENT_LINK_SEARCH
    success_view = "documents:table_document_links"
    operation = "delete"
    form_class = EmptyForm


