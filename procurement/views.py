import json
from pkgutil import extend_path
from urllib.parse import urlencode

from django.db import transaction
from django.contrib import messages
from django.db.models.deletion import ProtectedError

from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.views import View

from documents.models import TblDocumentLinks, TblDocumentTypes, TemporaryUpload
from documents.utils import get_extraction_results, save_extraction_results
from documents.views import SaveTempFiles

# import Models
from .models import (
    TblInvoices,
    TblPurchaseOrder,
    TblPoLines,
    PoView,
    PoView,
    Outstandngdeliveriesview,
    TblDeliveries,
    TblDeliveryLines,
)

# import class based views
from django_filters.views import FilterView
from django.views.generic import (
    UpdateView,
    CreateView,
    DeleteView,
    ListView,
    DetailView,
    TemplateView,
    FormView,
)


from .forms import PoCreateForm, PoLineFormset, DeliveryLineFormset, InvoiceCreateForm


# import permission and login mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# import generic filter table view
from utils.generic_views import FilteredTableView


# import miscellaneous tools
from functools import reduce
import operator
import ast

from .reports.purchase_order import print_po


# Create your views here.
# Purchase order views
class PoTableView(LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView):
    model = TblPurchaseOrder
    paginate_by = 20
    permission_required = "procurement.view_tblpurchaseorder"
    template_name = "procurement/purchaseorders.html"
    template_columns = {"open": "procurement/tables/open_po.html"}
    universal_search_fields = {
        "po_id__icontains",
        "supplier__supplier_name__icontains",
    }


class PoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TblPurchaseOrder
    template_name = "procurement/po_create.html"
    form_class = PoCreateForm
    permission_required = "procurement.add_tblpurchaseorder"

    def get_success_url(self):
        return reverse("procurement:po_update", kwargs={"pk": self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial["date_raised"] = now().date().isoformat()
        return initial


class PoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TblPurchaseOrder
    template_name = "procurement/po_update.html"
    form_class = PoCreateForm
    permission_required = "procurement.change_tblpurchaseorder"

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = PoLineFormset(self.request.POST, instance=self.object)
        else:
            supplier_id = self.object.supplier_id
            context["formset"] = PoLineFormset(
                instance=self.object, supplier_id=supplier_id
            )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = PoLineFormset(
            self.request.POST, instance=self.object
        )  # You'll need to define this

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        formset.instance = self.object
        formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        context = self.get_context_data(form=form)
        context["formset"] = formset
        return self.render_to_response(context)


class PoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblPurchaseOrder
    template_name = "procurement/po_detail.html"
    context_object_name = "po"
    permission_required = "procurement.view_tblpurchaseorder"


class PoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TblPurchaseOrder
    success_url = reverse_lazy("procurement:po")
    template_name = "procurement/po_delete.html"
    context_object_name = "po"
    permission_required = "procurement.delete_tblpurchaseorder"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            response = HttpResponse()
            messages.warning(request, f"PO deleted")

            response["HX-Redirect"] = self.success_url
            return response
        except Exception as e:
            context = self.get_context_data(object=self.object)
            messages.warning(request, f"Error Details: {str(e)}")
            return self.render_to_response(context)


# PO lines views
class PoLinesListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TblPoLines
    context_object_name = "po_lines"
    template_name = "procurement/partials/polines.html"
    permission_required = "procurement.view_tblpolines"

    def get_queryset(self):
        po = self.request.GET.get("po")
        queryset = TblPoLines.objects.filter(po=po)
        return queryset


# PO lines views
class GeneratePurchaseOrder(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblPurchaseOrder
    context_object_name = "po_lines"
    permission_required = "procurement.view_tblpurchaseorder"

    def get(self, request, *args, **kwargs):
        po_lines = PoView.objects.filter(po_id=self.get_object().po_id)
        return print_po(po_lines)


# Deliveries
class DeliveriesListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TblDeliveries
    context_object_name = "deliveries"
    template_name = "procurement/partials/deliveries.html"
    permission_required = "procurement.view_tbldeliveries"

    def get_queryset(self):
        po = self.request.GET.get("po")
        delivery_id = self.request.GET.get("delivery_id")

        if po:
            return TblDeliveries.objects.filter(po=po)

        elif delivery_id:
            return TblDeliveries.objects.filter(delivery_id=delivery_id)


class DeliveryLinesListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TblDeliveryLines
    context_object_name = "del_lines"
    template_name = "procurement/partials/delivery_lines.html"
    permission_required = "procurement.view_tbldeliveries"

    def get_queryset(self):
        delivery_id = self.request.GET.get("delivery_id")

        queryset = TblDeliveryLines.objects.filter(delivery=delivery_id)
        return queryset


# Deliveries
class OutstandingItemsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Outstandngdeliveriesview
    context_object_name = "outstanding_items"
    template_name = "procurement/partials/outstanding_items.html"
    permission_required = [
        "procurement.view_tbldeliveries",
        "procurement.view_tblpurchaseorder",
    ]

    def get_queryset(self):
        po = self.request.GET.get("po")
        queryset = Outstandngdeliveriesview.objects.filter(po_id=po)
        return queryset


class DeliveryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TblDeliveries
    template_name = "procurement/po_delivery.html"
    fields = "__all__"
    permission_required = "procurement.add_tbldeliveries"

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.po_id})

    def get_initial(self):
        initial = super().get_initial()
        initial["delivery_date"] = now().date().isoformat()

        # get po_id from get kwargs
        po_id = self.request.GET.get("po_id")
        if po_id:
            po = TblPurchaseOrder.objects.get(po_id=po_id)
            initial["po"] = po

        # get delivery_note_number from get kwargs
        delivery_note_number = self.request.GET.get("delivery_note_number")

        if delivery_note_number:
            initial["delivery_note_number"] = delivery_note_number
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = DeliveryLineFormset(
                self.request.POST, instance=self.object
            )
        else:
            po_id = self.request.GET.get("po_id")
            outstanding_items = Outstandngdeliveriesview.objects.filter(po_id=po_id)
            context["temp_file_group"] = self.request.GET.get("temp_file_group")
            initial = []
            delivered_items = self.request.GET.get("items", None)
            if delivered_items:
                delivered_items = ast.literal_eval(delivered_items)

            for item in outstanding_items:
                delivered_item = {}
                delivered_item["item"] = item.item_id
                try:
                    delivered_item["qty"] = int(
                        [
                            d.get("qty")
                            for d in delivered_items
                            if d["item"] == item.part_number
                        ][0]
                    )
                except:
                    delivered_item["qty"] = item.outstanding
                initial.append(delivered_item)

            context["formset"] = DeliveryLineFormset(
                instance=self.object, initial=initial, extra=len(initial) + 2
            )

        return context

    def post(self, request, *args, **kwargs):
        self.object = None  # Important for CreateView
        form = self.get_form()
        formset = DeliveryLineFormset(self.request.POST)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            temp_file_group = self.request.POST.get("temp_file_group")

            if temp_file_group and temp_file_group != "None":
                files = TemporaryUpload.objects.filter(
                    user=self.request.user, group=temp_file_group
                )
                if files:
                    delivery_note_file = SaveTempFiles(
                        temp_files=files,
                        content_object=self.object,
                        document_type=TblDocumentTypes.objects.filter(
                            document_type_name="Delivery Note"
                        ).first(),
                        file_name=f"delivery_note_{self.object.pk}",
                    )
                    delivery_note_file.save_all()
            messages.success(self.request, "Delivery note created successfully.")

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        context = self.get_context_data(form=form, formset=formset)
        return self.render_to_response(context)


class DeliveryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TblDeliveries
    template_name = "procurement/delivery_update.html"
    fields = "__all__"
    permission_required = "procurement.change_tbldeliveries"

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.po})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = DeliveryLineFormset(
                self.request.POST, instance=self.object
            )
        else:
            po = self.object.po.po_id
            context["formset"] = DeliveryLineFormset(instance=self.object, po=po)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        po = self.object.po.po_id
        formset = DeliveryLineFormset(
            self.request.POST, instance=self.object, po=po
        )  # You'll need to define this
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        formset.instance = self.object
        formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        context = self.get_context_data(form=form)
        context["formset"] = formset
        return self.render_to_response(context)


class DeliveryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TblDeliveries
    permission_required = "procurement.delete_tbldeliveries"
    template_name = "procurement/partials/delivery_delete_view.html"

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.po_id})

    def form_valid(self, form):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            messages.success(self.request, "Delivery deleted successfully")
            if self.request.htmx:
                return render(
                    self.request, "partials/messages.html", status=200
                )  # HTMX expects 200 OK even if empty

            # Fallback redirect if not HTMX
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError:
            messages.warning(
                self.request,
                "This item cannot be deleted because it is linked to other records.",
            )
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)


class DeliveryNoteReader(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "procurement.change_tbldeliveries"
    template_name = "procurement/partials/delivery_note_reader.html"

    def post(self, request, *args, **kwargs):
        return self.form_valid(request.POST)

    def get_success_url(self, **kwargs):
        return reverse(
            "procurement:delivery_note_reader_output",
            kwargs={"temp_file_group": self.group},
        )

    def form_valid(self, form):
        self.group = self.kwargs.get("temp_file_group")
        files = TemporaryUpload.objects.filter(user=self.request.user, group=self.group)
        from .utils.document_reader import delivery_note_reader

        output = delivery_note_reader(files)
        if len(output) == 0:
            messages.warning(self.request, "No Delivery Information found")
            return render(self.request, "partials/messages.html", context=None)
        output["document_type"] = "delivery_note"
        save_extraction_results(
            user_id=self.request.user, group=self.group, results=output, hours=1
        )

        response = HttpResponse()
        response["HX-Redirect"] = self.get_success_url()
        return response


class DeliveryNoteReaderOutput(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    template_name = "procurement/partials/delivery_note_reader_output.html"
    permission_required = "procurement.change_tbldeliveries"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.group = self.kwargs.get("temp_file_group")

        context["temp_file_group"] = self.group

        output = get_extraction_results(user_id=self.request.user, group=self.group)
        if not output:
            context["error"] = "No delivery note data found."
        else:
            context["output"] = output
            # lookup PO in database
            po_id = output.get("po", "")
            if po_id:
                po = TblPurchaseOrder.objects.filter(po_id=po_id).first()

                if po:
                    context["po_id"] = po
                else:
                    context["error"] = "Purchase order not recognised"

            # lookup deliverynote in database
            delivery_note = output.get("DelNote", "")
            if delivery_note:
                delnotes = TblDeliveries.objects.filter(
                    delivery_note_number__icontains=delivery_note
                )
                if delnotes.exists():
                    context["existing_delivery"] = delnotes[0]
                else:
                    context["new_delivery_required"] = "true"
        return context


# invoices
class FilteredInvoiceTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = TblInvoices
    paginate_by = 25
    permission_required = "procurement.view_tblinvoices"
    template_name = "procurement/invoices_table.html"
    template_columns = {"open": "procurement/tables/open_invoice.html"}
    universal_search_fields = [
        "invoice_id__icontains",
        "invoice_no__icontains",
        "po__po_id__icontains",
        "invoice_status__invoice_status_name__icontains",
    ]
    exclude = []


class InvoicesCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TblInvoices
    template_name = "procurement/invoices_create.html"
    form_class = InvoiceCreateForm
    permission_required = "procurement.add_tblinvoices"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["temp_file_group"] = self.request.GET.get("temp_file_group")
        return context

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.po})

    def get_initial(self):
        initial = super().get_initial()
        temp_file_group = self.request.GET.get("temp_file_group")

        invoice_reader_output = get_extraction_results(
            self.request.user, temp_file_group
        )

        if invoice_reader_output:
            for key, value in invoice_reader_output.items():
                initial[key] = value
        else:
            for key, value in self.request.GET.items():
                initial[key] = value

        initial["creation_date"] = now().date().isoformat()
        return initial

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            temp_file_group = self.request.POST.get("temp_file_group", None)
            if temp_file_group and temp_file_group != "None":
                files = TemporaryUpload.objects.filter(
                    user=self.request.user, group=temp_file_group
                )
                if files:
                    invoice_file = SaveTempFiles(
                        temp_files=files,
                        content_object=self.object,
                        document_type=TblDocumentTypes.objects.filter(
                            document_type_name="Invoice"
                        ).first(),
                        file_name=f"invoice_'+{self.object.pk}",
                    )
                    invoice_file.save_all()

        return HttpResponseRedirect(self.get_success_url())


class InvoicesDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblInvoices
    template_name = "procurement/invoices_detail.html"
    form_class = InvoiceCreateForm
    permission_required = "procurement.add_tblinvoices"
    context_object_name = "invoice"


class InvoicesUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TblInvoices
    template_name = "procurement/invoices_create.html"
    form_class = InvoiceCreateForm
    permission_required = "procurement.change_tblinvoices"

    def get_success_url(self):
        return reverse(
            "procurement:invoices_detail", kwargs={"pk": self.object.invoice_id}
        )


class InvoicesDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TblInvoices
    template_name = "procurement/invoices_delete.html"
    permission_required = "procurement.delete_tblinvoices"
    context_object_name = "invoice"

    def get_success_url(self):
        return reverse("procurement:invoices_table")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            response = HttpResponseRedirect(self.get_success_url())
            return response
        except Exception as e:
            context = self.get_context_data(object=self.object)
            messages.warning(request, f"Error Details: {str(e)}")
            return self.render_to_response(context)


class InvoicesListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TblInvoices
    context_object_name = "invoices"
    template_name = "procurement/partials/invoices_list.html"
    permission_required = "procurement.view_tblinvoices"

    def get_queryset(self):
        qs = super().get_queryset()

        po = self.request.GET.get("po")

        if po:
            return qs.filter(po=po)
        return qs


class InvoiceReader(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "procurement.change_tblinvoices"
    template_name = "procurement/partials/delivery_note_reader.html"

    def post(self, request, *args, **kwargs):
        return self.form_valid(request.POST)

    def get_success_url(self, **kwargs):
        return reverse(
            "procurement:invoices_reader_output", kwargs={"temp_file_group": self.group}
        )

    def form_valid(self, form):
        self.group = self.kwargs.get("temp_file_group")
        files = TemporaryUpload.objects.filter(user=self.request.user, group=self.group)

        from .utils.invoice_reader import invoice_reader

        output = invoice_reader(files)
        if len(output) == 0:
            messages.warning(self.request, "No Invoice Information found")
            return render(self.request, "partials/messages.html", context=None)

        output["document_type"] = "invoice"
        save_extraction_results(
            user_id=self.request.user, group=self.group, results=output, hours=1
        )

        response = HttpResponse()
        response["HX-Redirect"] = self.get_success_url()
        return response


class InvoiceReaderOutput(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "procurement/partials/invoice_reader_output.html"
    permission_required = "procurement.change_tblinvoices"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.group = self.kwargs.get("temp_file_group")
        output = get_extraction_results(user_id=self.request.user, group=self.group)

        if self.group:
            context["temp_file_group"] = self.group

        if not output:
            context["error"] = "No invoice data found."
        else:
            context["output"] = output
            # lookup PO in database
            po_id = output.get("po", "")
            if po_id:
                po = TblPurchaseOrder.objects.filter(po_id=po_id).first()
                if po:
                    context["po_id"] = po
                else:
                    context["error"] = "Purchase order not recognised"

            # lookup invoice in database
            invoice_no = output.get("invoice_no", "")
            if invoice_no:
                invoice = TblInvoices.objects.filter(
                    invoice_no__icontains=invoice_no
                ).first()
                if invoice:
                    context["existing_invoice"] = invoice
                else:
                    context["new_invoice_required"] = "true"
        return context
