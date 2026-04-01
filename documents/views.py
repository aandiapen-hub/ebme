from io import BytesIO
from urllib.parse import urlencode
from django.apps import apps
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, render
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, Http404
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.views import View
from django.core.exceptions import ValidationError
from .service import create_document_from_file, save_temp_files, delete_link_document

# import models
from .models import (
    TblDocuments,
    TblDocumentLinks,
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
    TemplateView,
)

# import forms
from .forms import (
    DocumentLinkCreateForm,
    DocumentUpdateForm,
    TempFileUploadForm,
    QuickScannerForm,
    LinkTemporaryDocumentForm,
    DocumentLinkUpdateForm,
)

# import generic filter table view
from utils.generic_views import FilteredTableView
from django.db.models import ForeignKey


# import mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .mixins import DocumentLinkPermissionMixin
from pdf2image import convert_from_path
from .utils import clear_extraction_results, save_extraction_results
from .utils import get_extraction_results


# Create your views here.


class DocumentAndLinkCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = TblDocuments
    form_class = DocumentLinkCreateForm
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
        try:
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

        except Exception as e:
            if "unique_has" in str(e):
                import hashlib

                uploaded_file.seek(0)
                dup_hash = hashlib.sha256(uploaded_file.read()).hexdigest()
                existing_doc = TblDocuments.objects.filter(
                    document_hash=dup_hash
                ).first()
                messages.warning(
                    self.request,
                    f"Document already exists in Database.Existing document id: {existing_doc.pk}",
                )
            else:
                messages.warning(self.request, f"Error:{str(e)}")
            return self.form_invalid(form)


class DocumentLinkDeleteView(
    LoginRequiredMixin, DocumentLinkPermissionMixin, DeleteView
):
    model = TblDocumentLinks
    template_name = "documents/partials/document_crud_modal.html"
    permission_required = "documents.delete_tbldocumentlinks"

    success_url = reverse_lazy("documents:table_document_links")  # or wherever you want

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        delete_link_document(self.object)
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


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TblDocuments
    template_name = "documents/document_update.html"
    permission_required = "documents.change_tbldocuments"
    form_class = DocumentUpdateForm
    success_url = reverse_lazy("documents:table_document_links")

    def form_valid(self, form):
        uploaded_file = self.request.FILES.get("document_bytea")
        if uploaded_file:
            form.instance.document_bytea = uploaded_file.read()
            form.instance.mime_type = uploaded_file.content_type
            form.instance.file_size = uploaded_file.size
        return super().form_valid(form)


class DocumentLinksTableView(
    LoginRequiredMixin, DocumentLinkPermissionMixin, FilteredTableView
):
    model = TblDocumentLinks
    paginate_by = 20
    permission_required = "documents.view_tbldocumentlinks"
    template_name = "documents/documents_links.html"
    template_columns = {"actions": "documents/tables/document_links_buttons.html"}
    universal_search_fields = [
        "documentid__document_name__icontains",
        "documentid__icontains",
    ]
    exclude = ["document_bytea"]


class DocumentsTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = TblDocuments
    paginate_by = 20
    permission_required = "documents.view_tbldocuments"
    template_name = "documents/documents.html"
    template_columns = {"actions": "documents/tables/documents_buttons.html"}
    universal_search_fields = [
        "document_name__icontains",
        "document_description__icontains",
        "document_id__icontains",
    ]
    exclude = ("document_bytea",)


class DocumentDownloadView(LoginRequiredMixin, DocumentLinkPermissionMixin, DetailView):
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
        print("document links count", document_links.count())

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


class DocumentPreView(LoginRequiredMixin, View):
    def get(self, request):
        pk = request.GET.get("pk")
        user = request.user
        try:
            temp_upload = TemporaryUpload.objects.get(pk=pk, user=user)
        except TemporaryUpload.DoesNotExist:
            raise Http404("File not found or is not yours")
        mime_type = temp_upload.mime_type
        if mime_type == "application/pdf":
            page = convert_from_path(temp_upload.file.path, first_page=1, last_page=1)
            image = page[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            return FileResponse(buffer, content_type="image/png")
        return FileResponse(temp_upload.file.open("rb"), content_type=mime_type)


class TempFilesDeleteAllView(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy("documents:user_temp_files")

    def post(self, request, *args, **kwargs):
        user = request.user
        files = TemporaryUpload.objects.filter(user=user)
        for f in files:
            f.delete()

        return HttpResponseRedirect(self.success_url)


class TempFilesDeleteView(LoginRequiredMixin, DeleteView):
    model = TemporaryUpload
    success_url = reverse_lazy("documents:user_temp_files")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user == self.object.user:
            self.object.delete()

        # HTMX request → empty response
        if request.htmx:
            response = HttpResponse(status=200)

            if not TemporaryUpload.objects.filter(
                group=self.object.group, user=request.user
            ).exists():
                response["HX-Retarget"] = f"#group_{self.object.group}"

            return response  # No Content

        return HttpResponseRedirect(self.success_url)


class TemporaryUploadCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = TemporaryUpload
    template_name = "documents/partials/temp_document_create.html"
    form_class = TempFileUploadForm
    permission_required = "documents.add_tbl_temporaryupload"

    def form_valid(self, form):
        file = self.request.FILES.get("files")
        raw_group = self.request.POST.get("group")

        groups = list(
            TemporaryUpload.objects.filter(user=self.request.user).values_list(
                "group", flat=True
            )
        )

        if groups:
            latest_group = max(groups)
        else:
            latest_group = 0
        # cases when group is 'new' or a group is specified. otherwise the latest group will be used.
        if raw_group:
            try:
                group = int(raw_group)
                group_content_type = (
                    TemporaryUpload.objects.filter(group=group).first().mime_type
                )
                if (
                    "image" not in group_content_type
                    or "image" not in file.content_type
                ):
                    return self.form_invalid(form)

            except:
                if "new" in raw_group:
                    group = latest_group + 1

        else:
            group = latest_group

        object = TemporaryUpload.from_uploaded_file(
            user=self.request.user,
            file=file,
            group=group,
        )

        if self.request.htmx:
            group_document_count = TemporaryUpload.objects.filter(
                user=self.request.user, group=object.group
            ).count()
            if group_document_count == 1:
                context = {"group": object.group, "temp_files": [object]}
                return render(
                    self.request,
                    "documents/partials/temp_file_group.html",
                    context=context,
                )
            else:
                context = {"file": object}
                return render(
                    self.request, "documents/partials/temp_file.html", context
                )

        else:
            return HttpResponseRedirect(reverse("documents:create_temp_files"))

    def form_invalid(self, form):
        messages.warning(self.request, "Incorrect file type uploaded.")
        response = render(self.request, "partials/messages.html")
        response["HX-Retarget"] = "this"
        response["HX-Reswap"] = "beforeend"
        return response


class TempUploadDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TemporaryUpload
    template_name = "documents/partials/temp_file.html"
    context_object_name = "file"
    permission_required = "documents.view_tbl_temporaryupload"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise Http404("File not found or is not yours")
        return obj


class TempUploadListView(LoginRequiredMixin, ListView):
    model = TemporaryUpload
    template_name = "documents/temp_files_list.html"
    context_object_name = "temp_files_groups"
    permission_required = "documents.view_tbl_temporaryupload"

    def get_queryset(self):
        qs = super().get_queryset()

        group = self.request.GET.get("group")
        if group:
            user_qs = qs.filter(user=self.request.user, group=group)

        else:
            user_qs = qs.filter(user=self.request.user)
        if user_qs:
            grouped_qs = {}
            for obj in user_qs:
                key = getattr(obj, "group")
                if key not in grouped_qs:
                    grouped_qs[key] = []
                grouped_qs[key].append(obj)
                sorted_grouped_qs = dict(sorted(grouped_qs.items()))
            return sorted_grouped_qs

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
        print(model, object_id)
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
    form_class = QuickScannerForm
    template_name = "documents/quick_scanner.html"

    def form_valid(self, form):
        file = self.request.FILES.get("file")
        scanned_code = form.cleaned_data["scanned_code"]

        from .services.gs1_parser import process_barcode

        decoded_info = None
        try:
            decoded_info = process_barcode(file=file, scanned_code=scanned_code)
        except ValidationError as e:
            if hasattr(e, "message_dict"):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                messages.warning(self.request, str(e))
                form.add_error(None, e.message)

        if not self.request.user.is_staff:
            return self.redirect_non_staff(decoded_info.get("search_term"))

        return self.render_to_response(
            self.get_context_data(form=form, result=decoded_info)
        )

    def redirect_non_staff(self, search_term):
        base_url = reverse("assets:assets_list")
        qp = urlencode({"universal_search": search_term})
        return HttpResponseRedirect(f"{base_url}?{qp}")

    def form_invalid(self, form):
        return render(self.request, self.template_name, context={"form": form})

    def get_context_data(self, result=None, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["result"] = result
        return ctx


URL_MAP = {
    "device_id": "assets:barcode_output",
    "service_report": "jobs:report_reader_output",
    "invoice": "procurement:invoices_reader_output",
    "delivery_note": "procurement:delivery_note_reader_output",
}


class GetExtractedData(LoginRequiredMixin, TemplateView):
    template_name = "documents/partials/get_extracted_data.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.kwargs.get("group")
        if group:
            extracted_data = get_extraction_results(self.request.user, group)
            context["extracted_data"] = extracted_data
            context["group"] = group
            if extracted_data:
                document_type = extracted_data.get("document_type", None)
                if document_type:
                    context["action"] = reverse(
                        URL_MAP.get(document_type), kwargs={"temp_file_group": group}
                    )

        return context


class UpdateExtractedData(LoginRequiredMixin, TemplateView):
    template_name = "documents/update_extracted_data.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.kwargs.get("temp_file_group")
        if group:
            extracted_data = get_extraction_results(self.request.user, group)
            context["extracted_data"] = extracted_data
            context["group"] = group
        return context

    def post(self, request, *args, **kwargs):
        form = request.POST.dict()

        if "device_id" in form.get("document_type"):
            form["suggested_brands"] = request.POST.getlist("suggested_brands")
            form["suggested_categories"] = request.POST.getlist("suggested_categories")

        group = self.kwargs.get("temp_file_group")
        form.pop("csrfmiddlewaretoken")
        save_extraction_results(
            user_id=self.request.user, group=group, results=form, hours=1
        )

        URL_MAP = {
            "device_id": "assets:barcode_output",
            "service_report": "jobs:report_reader_output",
            "invoice": "procurement:invoices_reader_output",
            "delivery_note": "procurement:delivery_note_reader_output",
        }

        document_type = form.get("document_type")

        if document_type not in URL_MAP:
            raise ValueError(f"Unknown document type: {document_type}")

        url = reverse(URL_MAP.get(document_type), kwargs={"temp_file_group": group})

        return HttpResponseRedirect(url)


class ExtractedDateDeleteView(LoginRequiredMixin, View):
    def get_success_url(self):
        # Use self.object to access the updated object
        return reverse("documents:get_extracted_data", kwargs={"group": self.group})

    def post(self, request, *args, **kwargs):
        self.group = self.kwargs.get("group")
        user = request.user
        clear_extraction_results(user, self.group)
        return HttpResponseRedirect(self.get_success_url())
