from assets.views import UNIVERSAL_SEARCH_FIELDS
from django.utils.safestring import mark_safe
from django.db import transaction
from django.db.utils import IntegrityError
from urllib.parse import urlencode
from documents.mixins import TempUploadMixin
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now

from documents.services.documents import delete_object_document_links
from utils.generic_views import BulkUpdateView

from .models import Tblpartslist, Tblpartsprice, SparepartView, TblPartModel
from assets.models import Tblmodel


# import class based views
from django.views.generic import (
    UpdateView,
    CreateView,
    DeleteView,
    ListView,
    DetailView,
    FormView,
)


# import generic filter table view
from utils.generic_views import FilteredTableView, TableAction

# import form tools
from .forms import (
    AddPartPrice,
    UpdatePartPrice,
    PartsBulkUpdateForm,
    CreatePartModelLinkForm,
)

# import permission and login mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

UNIVERSAL_SEARCH_FIELDS = [
    "partid__icontains",
    "description__icontains",
    "part_number__icontains",
    "short_name__icontains",
    "supplier_name__icontains",
]
 
# Create your views here.
# part views
class PartsTableView(LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView):
    model = SparepartView
    title = 'Spare Parts'
    paginate_by = 20
    permission_required = "parts.view_tblpartslist"
    open_column = 'partid'
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    actions = [
        TableAction(
            name='Add',
            type='link',
            url=reverse_lazy('parts:create_part'),
            permission="parts.add_tblpartslist",
            icon='bi-plus',
            color='outline-secondary'
        ),
        TableAction(
            name="Update",
            type='bulk_htmx',
            url=reverse_lazy("parts:bulk_update_part"),
            permission="parts.change_tblpartslist",
            icon="bi-pencil",
            color='outline-secondary'
        ),
    ]

class PartDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblpartslist
    template_name = "parts/part_view.html"
    fields = "__all__"
    permission_required = "parts.view_tblpartslist"


class PartUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblpartslist
    fields = "__all__"
    template_name = "parts/update_part.html"
    permission_required = "parts.change_tblpartslist"

    def get_success_url(self):
        return reverse("parts:part_detail", kwargs={"pk": self.object.partid})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "parts:part_detail", kwargs={"pk": self.object.pk}
            )

        return context


class PartBulkUpdateView(BulkUpdateView):
    # filterset_class = PartFilter
    model = SparepartView
    permission_required = "parts.change_tblpartslist"
    template_name = 'parts/bulk_update_parts.html'
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    form_class = PartsBulkUpdateForm
    success_view = "parts:parts"
    table_to_update = Tblpartslist


class PartDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblpartslist
    template_name = "parts/delete_part.html"
    success_url = reverse_lazy("parts:parts")
    permission_required = "parts.delete_tblpartslist"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "parts:part_detail", kwargs={"pk": self.object.pk}
            )
        return context

    def form_valid(self, form):

        self.object = self.get_object()
        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()
            return HttpResponseRedirect(self.success_url)

        except ProtectedError:
            form.add_error(
                None,
                "This part cannot be deleted because it is still being used elsewhere.",
            )
            return self.form_invalid(form)


class PartCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TempUploadMixin, CreateView
):
    model = Tblpartslist
    fields = "__all__"
    template_name = "parts/create_part.html"
    permission_required = "parts.add_tblpartslist"
    initial_mapper = "create_part"
    success_url_app_view = "parts:part_detail"

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
                self.after_save(form)
        except IntegrityError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        part_number = form.cleaned_data["part_number"]
        supplier_id = form.cleaned_data["supplier_id"]
        existing_part = (
            Tblpartslist.objects.filter(part_number=part_number)
            .filter(supplier_id=supplier_id)
            .first()
        )
        if existing_part:
            url = reverse("parts:part_detail", kwargs={"pk": existing_part.partid})
            form.add_error(
                None,
                mark_safe(
                    f'This part number from the same supplier already exists - <a href="{url}">Go to Existing Part</a>'
                ),
            )
        return super().form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse("parts:parts")

        return context


class SparePartPriceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices.html"
    context_object_name = "price_list"
    permission_required = "parts.view_tblpartsprice"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["partid"] = self.request.GET.get("partid", None)
        return context

    def get_queryset(self, **kwargs):
        qs = super().get_queryset()
        partid = self.request.GET.get("partid", None)
        if partid:
            return super().get_queryset().filter(partid=partid)
        return qs


class SparePartPriceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices_create.html"
    form_class = AddPartPrice
    permission_required = "parts.add_tblpartsprice"

    def get_success_url(self):
        return reverse("parts:part_prices_detail", kwargs={"pk": self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        partid = self.request.GET.get("partid", None)
        initial["partid"] = partid
        initial["effectivedate"] = now().date().isoformat()
        return initial

    def form_valid(self, form):
        try:
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            context = self.get_context_data(object=self.object)
            context["error_message"] = (
                f"An error occurred while adding price. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


class SparePartPriceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices.html#part_price"
    fields = "__all__"
    context_object_name = "part_price"
    permission_required = "parts.view_tblpartsprice"


class SparePartPriceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices_delete.html"
    fields = "__all__"
    permission_required = "parts.delete_tblpartsprice"

    def get_success_url(self):
        base_url = reverse("parts:part_prices")
        query_string = urlencode({"partid": self.object.partid.partid})
        return f"{base_url}?{query_string}"

    def post(self, request, *args, **kwargs):
        # Set self.object before the usual form processing flow.
        # Inlined because having DeletionMixin as the first base, for
        # get_success_url(), makes leveraging super() with ProcessFormView
        # overly complex.
        self.object = self.get_object()

        with transaction.atomic():
            delete_object_document_links(self.object)
            self.object.delete()
        if request.htmx:
            return HttpResponse("")
        return HttpResponseRedirect(self.get_success_url())


class SparePartPriceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblpartsprice
    template_name = "parts/partials/part_prices_update.html"
    form_class = UpdatePartPrice
    permission_required = "parts.change_tblpartsprice"

    def get_success_url(self):
        return reverse("parts:part_prices_detail", kwargs={"pk": self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial["effectivedate"] = self.object.effectivedate.isoformat()
        return initial


# model link views


class PartLinkedModelListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TblPartModel
    template_name = "parts/partials/linked_models.html"
    context_object_name = "linked_models"
    permission_required = "parts.view_tblpartmodel"

    def get_queryset(self, **kwargs):
        qs = super().get_queryset()
        partid = self.request.GET.get("partid", None)
        if partid:
            return super().get_queryset().filter(part=partid)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["partid"] = self.request.GET.get("partid")
        return context


class LinkModelCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    model = Tblmodel
    permission_required = "parts.add_tblpartmodel"
    template_name = "parts/partials/linked_model_create.html"
    form_class = CreatePartModelLinkForm

    def get_success_url(self):
        return reverse("parts:part_detail", kwargs={"pk": self.partid})

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        partid = self.request.GET.get("partid")
        initial["partid"] = partid
        return initial

    def form_valid(self, form):
        models = form.cleaned_data["models"]
        self.partid = form.cleaned_data["partid"]

        part = Tblpartslist.objects.get(partid=self.partid)

        existing = set(
            TblPartModel.objects.filter(part=self.partid).values_list(
                "model", flat=True
            )
        )

        new = [
            TblPartModel(model=model, part=part)
            for model in models
            if model.pk not in existing
        ]

        if new:
            with transaction.atomic():
                TblPartModel.objects.bulk_create(new)

        return HttpResponseRedirect(self.get_success_url())


class LinkModelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TblPartModel
    template_name = "parts/partials/linked_model_delete.html"
    permission_required = "parts.delete_tblpartmodel"
    success_url = reverse_lazy("parts:linked_models")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.object.delete()
        if request.htmx:
            return HttpResponse("")
        return HttpResponseRedirect(self.success_url)


class LinkedModelDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TblPartModel
    template_name = "parts/partials/linked_models.html#linked_model"
    fields = "__all__"
    context_object_name = "link"
    permission_required = "parts.view_tblpartmodel"
