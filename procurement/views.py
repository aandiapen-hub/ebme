from django.db import transaction

from django.db.models.deletion import ProtectedError
import json
from django.contrib import messages
from utils.dynamic_formset import (
    AddFormsetRowView,
    FormsetOptionsListView,
    FormsetMixin,
)
from documents.services.payloads import (
    get_formset_initial,
)
from documents.mixins import TempUploadMixin

from .services.delivery_note import delivery_items_formset_get_context

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from parts.models import Tblpartslist

from documents.services.documents import (
    delete_object_document_links,
)

# import Models
from .models import (
    TblInvoices,
    TblPurchaseOrder,
    PoView,
    TblDeliveries,
)

# import class based views
from django.views.generic import (
    UpdateView,
    CreateView,
    DeleteView,
    DetailView,
)


from .forms import (
    PoCreateForm,
    PoLineFormset,
    DeliveryLineFormset,
    InvoiceCreateForm,
    DeliveryCreateForm,
)

# import permission and login mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# import generic filter table view
from utils.generic_views import FilteredTableView

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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["cancel_url"] = reverse("procurement:po")

        return context


PO_FORMSET_CONFIG = {
    "po_line": {
        "prefix": "po_line",
        "row_template_name": None,
        "formset": PoLineFormset,
        "model": Tblpartslist,
        "pk_field": "partid",
        "lookup_field": "item",
        "lookup_view": "procurement:po_item_option_list",
        "lookup_query_params": {"supplier_id": lambda view: view.object.supplier.pk},
        "title": "Items",
        "initial": lambda obj: {
            "item": obj.pk,
            "quantity": 1,
        },
    },
}


class PoItemOptionListView(FormsetOptionsListView):
    model = Tblpartslist
    permission_required = "procurement.change_tblpurchaseorder"
    config = PO_FORMSET_CONFIG
    add_formset_row_view = "procurement:add_formset_row"

    def get_queryset(self):
        qs = super().get_queryset()
        supplier_id = self.request.GET.get("supplier_id", None)
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs


class PoAddFormsetRowView(AddFormsetRowView):
    permission_required = "procurement.change_tblpurchaseorder"
    formset_config = PO_FORMSET_CONFIG


class PoUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormsetMixin,
    UpdateView,
):
    model = TblPurchaseOrder
    template_name = "procurement/po_update.html"
    form_class = PoCreateForm
    permission_required = "procurement.change_tblpurchaseorder"
    config = PO_FORMSET_CONFIG

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(super().get_formsets())
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "procurement:po_detail", kwargs={"pk": self.object.po_id}
            )
        return context

    def form_valid(self, form):
        super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())


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

    def form_valid(self, form):
        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()
            response = HttpResponseRedirect(self.success_url)

            return response
        except ProtectedError:
            form.add_error(
                None,
                "This part cannot be deleted because it is still being used elsewhere.",
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "procurement:po_detail", kwargs={"pk": self.object.po_id}
            )
        return context


class GeneratePurchaseOrder(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblPurchaseOrder
    context_object_name = "po_lines"
    permission_required = "procurement.view_tblpurchaseorder"

    def get(self, request, *args, **kwargs):
        po_lines = PoView.objects.filter(po_id=self.get_object().po_id)
        return print_po(po_lines)


class DeliveryCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TempUploadMixin, CreateView
):
    model = TblDeliveries
    template_name = "procurement/delivery_create.html"
    form_class = DeliveryCreateForm
    permission_required = "procurement.add_tbldeliveries"

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.po_id})

    def get_initial(self):
        initial = super().get_initial()
        initial["po"] = self.kwargs.get("po_id")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = DeliveryLineFormset(
                self.request.POST, instance=self.object
            )
        else:
            formset_data = delivery_items_formset_get_context(
                po_id=self.kwargs.get("po_id", None),
                instance=self.object,
                formset_class=DeliveryLineFormset,
                delivered_items=get_formset_initial(self.get_temp_group_id()),
            )
            context.update(**formset_data)

        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "procurement:po_detail", kwargs={"pk": self.kwargs.get("po_id")}
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

            self.after_save(form)

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

        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "procurement:po_detail", kwargs={"pk": self.object.po_id}
            )
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
        with transaction.atomic():
            delete_object_document_links(self.object)
            self.object.delete()
        messages.success(self.request, "Delivery deleted successfully")
        if self.request.htmx:
            response = HttpResponse(status=200)
            response["HX-Trigger"] = json.dumps(
                {
                    "deliveries_updated": True,
                    "show_message": {
                        "message": "Delivery deleted",
                        "level": "warning",
                    },
                }
            )
            return response

        # Fallback redirect if not HTMX
        return HttpResponseRedirect(self.get_success_url())


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
        return context

    def get_success_url(self):
        return reverse("procurement:po_detail", kwargs={"pk": self.object.po})

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())


class InvoicesDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblInvoices
    template_name = "procurement/invoices_detail.html"
    form_class = InvoiceCreateForm
    permission_required = "procurement.view_tblinvoices"
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

    def form_valid(self, form):
        self.object = self.get_object()
        with transaction.atomic():
            delete_object_document_links(self.object)
            self.object.delete()
        response = HttpResponseRedirect(self.get_success_url())
        return response
