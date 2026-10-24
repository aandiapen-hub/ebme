from assets.views import UNIVERSAL_SEARCH_FIELDS
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    FormView,
    View,
)
from django_filter_table.views import FilteredTableView, TableAction
from django_filter_table.utils import add_htmx_message

from .models import (
    AuditLocation,
    InventoryAudit,
    AuditItem,
    CatalogProposal,
    AssetChangeProposal,
)
from .forms import (
    InventoryAuditForm,
    ModelProposalForm,
    BrandProposalForm,
    CategoryProposalForm,
    AssetChangeProposalForm,
    EmptyForm
)
from . import services


class AuditListView(
    LoginRequiredMixin,
    FilteredTableView,
):
    title = 'Audits'
    model = InventoryAudit
    open_column = 'reference'
    permission_required = "audits.view_inventoryaudit"
    universal_search_fields = [
        'name__icontains',
    ]

    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('audits:audit_create'),
            permission='assets.add_tblassets',
            icon='bi-plus',
            color='outline-secondary'
        ),
    ]

class AuditCreateView(
    LoginRequiredMixin,
    CreateView,
):
    form_class = InventoryAuditForm
    template_name = "audits/audit_create.html"
    permission_required = "audits.add_inventoryaudit"

    def form_valid(self, form):
        try:
            audit = services.create_audit(
                name=form.cleaned_data["name"],
                locations=form.cleaned_data["locations"],
                created_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Audit created successfully.")
        return redirect("audits:audit_detail", pk=audit.pk)

class AuditDetailView(
    LoginRequiredMixin,
    DetailView,
):
    model = InventoryAudit
    template_name = "audits/audit_detail.html"
    context_object_name = "audit"
    permission_required = "audits.view_inventoryaudit"

    def get_queryset(self):
        return InventoryAudit.objects.prefetch_related(
            "audit_locations__location",
            "audit_locations__items",
        )

class AuditLocationDetailView(
    LoginRequiredMixin,
    DetailView,
):
    model = AuditLocation
    template_name = 'audits/audit_location_detail.html'
    context_object_name = 'audit_location'
    permission_required = "audits.view_auditlocation"

class AuditLocationListView(
    LoginRequiredMixin,
    FilteredTableView,
):
    title = 'Audit Locations'
    model = AuditLocation
    open_column = 'Location'
    permission_required = "audits.view_auditlocation"
    universal_search_fields = [
        'audit__name__icontains',
        'location__icontains'
    ]


class AuditItemListView(
    LoginRequiredMixin,
    FilteredTableView,
):
    title = 'Audit Items'
    model = AuditItem
    open_column = 'asset'
    permission_required = "audits.view_audititem"
    universal_search_fields = [
        'original_serial_number__icontains',
        'audit_location__icontains'
    ]

class AuditItemDetailView(
    LoginRequiredMixin,
    DetailView,
):
    model = AuditItem
    template_name = 'audits/audit_item_detail.html'
    context_object_name = 'audit_item'
    permission_required = "audits.view_audititem"

class AuditItemVerifiedView(
    LoginRequiredMixin,
    FormView,
):
    model = AuditItem
    template_name = 'audits/audit_item_verified.html'
    form_class = EmptyForm
    permission_required = "audits.change_audititem"

    def form_valid(self, form):
        audit_item_id = self.kwargs.get('pk')
        audit_item = AuditItem.objects.get(pk=audit_item_id)
        try:
            services.audit_item_verified(audit_item=audit_item)
        except Exception as e:
            form.add_error(None, e)
            return self.form_invalid(form)

        return HttpResponseRedirect(
            reverse('audits:audit_item_detail', kwargs={'pk':audit_item_id})
        )


class ModelProposalCreateView(
    LoginRequiredMixin,
    FormView,
):
    form_class = ModelProposalForm
    template_name = "audits/model_proposal_create.html"
    permission_required = "audits.add_catalogproposal"

    def form_valid(self, form):
        data = form.cleaned_data

        try:
            proposal = services.submit_model_proposal(
                proposed_name=data["proposed_name"],
                proposed_model_number=data.get("proposed_model_number"),
                proposed_model_gtin=data.get("proposed_model_gtin"),
                brand=data.get("brand"),
                category=data.get("category"),
                discovered_in=data.get("discovered_in"),
                proposed_by=self.request.user,
            )
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Model proposal submitted. It is available to other auditors.",
        )

        return redirect("audits:catalog_proposal_detail", pk=proposal.pk)

class BrandProposalCreateView(
    LoginRequiredMixin,
    FormView,
):
    form_class = BrandProposalForm
    template_name = 'audits/brand_proposal_create.html'
    permission_required = "audits.add_catalogproposal"

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            proposal = services.submit_brand_proposal(
                proposed_name = data['proposed_name'],
                discovered_in=data.get("discovered_in"),
                proposed_by=self.request.user,
            )
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Brand proposal submitted. It is available to other auditors.",
        )

        return redirect("audits:catalog_proposal_detail", pk=proposal.pk)

class CategoryProposalCreateView(
    LoginRequiredMixin,
    FormView,
):
    form_class = CategoryProposalForm
    template_name = 'audits/category_proposal_create.html'
    permission_required = "audits.add_catalogproposal"

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            proposal = services.submit_category_proposal(
                proposed_name = data['proposed_name'],
                discovered_in=data.get("discovered_in"),
                proposed_by=self.request.user,
            )
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Category proposal submitted. It is available to other auditors.",
        )

        return redirect("audits:catalog_proposal_detail", pk=proposal.pk)

class CatalogProposalListView(
    LoginRequiredMixin,
    FilteredTableView,
):
    model = CatalogProposal
    open_column = 'proposed_name'
    permission_required = "audits.view_catalogproposal"
    paginate_by = 50
    universal_search_fields = [
        'proposed_name__icontains'
    ]
class CatalogProposalDetailView(
    LoginRequiredMixin,
    DetailView
):
    model = CatalogProposal
    template_name = 'audits/catalog_proposal_detail.html'
    context_object_name = 'proposal'


class CatalogProposalReviewView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    permission_required = "audits.change_catalogproposal"

    def post(self, request, pk):
        decision = request.POST.get("decision")

        try:
            services.review_catalog_proposal(
                proposal_id=pk,
                reviewer=request.user,
                decision=decision,
            )
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            if decision == "approve":
                messages.success(
                    request,
                    "Catalogue proposal approved and applied.",
                )
            else:
                messages.success(request, "Catalogue proposal rejected.")

        return redirect(
            "audits:catalog_proposal_detail",
            pk=pk,
        )

class AssetChangeProposalCreateView(
    LoginRequiredMixin,
    FormView,
):
    form_class = AssetChangeProposalForm
    template_name = "audits/audit_item_change_create.html"
    permission_required = "audits.add_assetchangeproposal"

    def form_valid(self, form):
        try:
            proposal = services.create_asset_change_proposal(
                audit_item_id=form.cleaned_data["audit_item"].pk,
                proposed_by=self.request.user,
                reason=form.cleaned_data["reason"],
                changes=form.cleaned_data["changes"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(
            self.request,
            "Asset change proposal submitted for review.",
        )

        return redirect("audits:asset_change_detail", pk=proposal.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_item'] = get_object_or_404(AuditItem, pk=self.kwargs['pk'])
        return context


class AssetChangeProposalReviewView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    permission_required = "audits.change_assetchangeproposal"

    def post(self, request, pk):
        decision = request.POST.get("decision")

        try:
            services.review_asset_change_proposal(
                proposal_id=pk,
                reviewer=request.user,
                decision=decision,
            )
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            if decision == "approve":
                messages.success(
                    request,
                    "Asset changes approved and applied.",
                )
            else:
                messages.success(request, "Asset changes rejected.")

        return redirect(
            "audits:asset_change_detail",
            pk=pk,
        )
