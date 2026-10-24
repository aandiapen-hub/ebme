from django.db import models
from django.urls import reverse
from django_filter_table.utils import HtmxPicker

# Create your models here.
# inventory_audit/models.py

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

class Status(models.TextChoices):
    DRAFT = "draft", "Draft"
    PROPOSED = "proposed", "Proposed"
    APPLIED = "applied", "Approved & Applied"
    REJECTED = "rejected", "Rejected"

class InventoryAudit(models.Model):

    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_inventory_audits",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory_audit'
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('audits:audit_detail', kwargs={'pk':self.pk}) 

class AuditLocation(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    audit = models.ForeignKey(
        InventoryAudit,
        on_delete=models.CASCADE,
        related_name="audit_locations",
    )

    location = models.ForeignKey(
        "assets.Tbllocations",
        on_delete=models.PROTECT,
        related_name="audits",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'audit_location'
        constraints = [
            models.UniqueConstraint(
                fields=["audit", "location"],
                name="unique_audit_location",
            )
        ]

    def __str__(self):
        return f"{self.audit.name} - {self.location}"


class CatalogProposal(models.Model):

    class EntityType(models.TextChoices):
        BRAND = "brand", "Brand"
        CATEGORY = "category", "Category"
        MODEL = "model", "Model"

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        APPLIED = "applied", "Applied"

    # Globally unique reference for the proposal.
    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    entity_type = models.CharField(
        max_length=20,
        choices=EntityType.choices,
        db_index=True,
    )

    proposed_name = models.CharField(max_length=255)

    # Optional manufacturer model number.
    proposed_model_number = models.CharField(
        max_length=100,
        blank=True,
    )
    proposed_model_gtin = models.CharField(
        max_length=100,
        blank=True,
    )

    # For category proposals: select an existing brand.
    proposed_brand = models.ForeignKey(
        'assets.Tblbrands',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="category_proposals",
    )

    # For model proposals: select an existing category.
    proposed_category = models.ForeignKey(
        'assets.Tblcategories',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="model_proposals",
    )

    # Allows a proposal to depend on a new brand.
    brand_proposal = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dependent_brand_proposals",
    )

    # Allows a proposal to depend on a new category.
    category_proposal = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dependent_category_proposals",
    )

    # The audit where this proposal was first discovered.
    # The proposal itself is not owned by that audit.
    discovered_in = models.ForeignKey(
        InventoryAudit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="discovered_catalog_proposals",
    )

    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="catalog_proposals",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROPOSED,
        db_index=True,
    )

    reason = models.TextField(blank=True)

    # The official record created or matched when applied.
    approved_brand = models.ForeignKey(
        'assets.Tblbrands',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_catalog_proposals",
    )

    approved_category = models.ForeignKey(
        'assets.Tblcategories',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_category_proposals",
    )

    approved_model = models.ForeignKey(
        'assets.Tblmodel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_model_proposals",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_catalog_proposals",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    applied_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalog_proposal'
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["entity_type", "status"],
                name="catalog_type_status_idx",
            ),
        ]

    def get_absolute_url(self):
        return reverse('audits:catalog_proposal_detail', kwargs={'pk':self.pk})

    def __str__(self):
        return f"{self.get_entity_type_display()}: {self.proposed_name}"

class AuditItem(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        DISCREPANCY = "discrepancy", "Discrepancy"
        NOT_FOUND = "not_found", "Not found"
        NEW_ASSET = "new_asset", "New asset"
        UNDER_REVIEW = "under_review", "Under review"
        RESOLVED = "resolved", "Resolved"

    audit = models.ForeignKey(
        InventoryAudit,
        on_delete=models.PROTECT,
        related_name="items",
    )

    audit_location = models.ForeignKey(
        AuditLocation,
        on_delete=models.PROTECT,
        related_name="items",
    )

    # Null for equipment not yet registered in the inventory.
    asset = models.ForeignKey(
        "assets.Tblassets",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_items",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Snapshot of the registered asset at audit creation time.
    original_asset_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    original_serial_number = models.CharField(
        max_length=100,
        blank=True,
    )

    original_model = models.ForeignKey(
        "assets.Tblmodel", models.PROTECT,  verbose_name="Model"
    )

    notes = models.TextField(blank=True)

    audited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="performed_audit_items",
    )

    audited_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_item'
        constraints = [
            models.UniqueConstraint(
                fields=["audit", "asset"],
                condition=Q(asset__isnull=False),
                name="unique_asset_per_inventory_audit",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        observed_model__isnull=True,
                        observed_model_proposal__isnull=True,
                    )
                    | Q(
                        observed_model__isnull=False,
                        observed_model_proposal__isnull=True,
                    )
                    | Q(
                        observed_model__isnull=True,
                        observed_model_proposal__isnull=False,
                    )
                ),
                name="audit_item_one_model_source",
            ),
        ]

    def __str__(self):
        return f"{self.audit.name} - {self.pk}"

    def is_complete(self):
        return self.status in ['verified', 'not_found', 'resolved']

    def get_absolute_url(self):
        return reverse('audits:audit_item_detail', kwargs={'pk':self.pk})


class AssetChangeProposal(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        PARTIALLY_APPROVED = (
            "partially_approved",
            "Partially approved",
        )
        REJECTED = "rejected", "Rejected"
        APPLIED = "applied", "Applied"
        NEEDS_REVIEW = "needs_review", "Needs re-review"

    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    audit_item = models.ForeignKey(
        AuditItem,
        on_delete=models.PROTECT,
        related_name="change_proposals",
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    reason = models.TextField()

    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_asset_change_proposals",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_asset_change_proposals",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    applied_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_change_proposal'
        ordering = ["-created_at"]

    def __str__(self):
        return f"Asset change {self.reference}"


class AssetFieldChange(models.Model):

    class FieldName(models.TextChoices):
        LOCATION = "location", "Location"
        MODEL = "model", "Model"
        ASSET_NUMBER = "asset_number", "Asset number"
        SERIAL_NUMBER = "serial_number", "Serial number"

    class Decision(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    proposal = models.ForeignKey(
        AssetChangeProposal,
        on_delete=models.PROTECT,
        related_name="changes",
    )

    field_name = models.CharField(
        max_length=30,
        choices=FieldName.choices,
    )

    # Store stable identifiers as well as display snapshots.
    old_value = models.JSONField()

    proposed_value = models.JSONField()

    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
        default=Decision.PENDING,
    )

    reviewer_comment = models.TextField(blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_asset_field_changes",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'asset_field_change'
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "field_name"],
                name="unique_field_per_asset_proposal",
            )
        ]

    def __str__(self):
        return f"{self.proposal.reference}: {self.field_name}"


class CombinedBrands(models.Model):
    id = models.CharField(
        max_length=100,
        primary_key=True
    )

    brand_name = models.CharField(
        max_length=100,
    )
    proposed = models.ForeignKey(
        CatalogProposal,
        models.PROTECT,
        null=True,
        blank=True
    )
    existing = models.ForeignKey(
        'assets.tblBrands',
        models.PROTECT,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'combined_brands'

    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=('brand_name__icontains',),
    )

    def __str__(self):
        if self.proposed:
            return f"{self.brand_name} (draft)"
        else:
            return str(self.brand_name)

class CombinedCategories(models.Model):
    id = models.CharField(
        max_length=100,
        primary_key=True
    )
    category_name = models.CharField(
        max_length=100,
    )
    proposed = models.ForeignKey(
        CatalogProposal,
        models.PROTECT,
        null=True,
        blank=True
    )
    existing = models.ForeignKey(
        'assets.tblcategories',
        models.PROTECT,
        null=True,
        blank=True
    )
    class Meta:
        db_table = 'combined_categories'

    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=('category_name__icontains',),
    )

    def __str__(self):
        if self.proposed:
            return f"{self.category_name} (draft)"
        else:
            return str(self.category_name)

class CombinedModels(models.Model):
    id = models.CharField(
        max_length=100,
        primary_key=True
    )
    
    model_name = models.CharField(
        max_length=100,
    )
    brand_name = models.CharField(
        max_length=100,
    )
    category_name = models.CharField(
        max_length=100,
    )
    existing = models.ForeignKey(
        'assets.Tblmodel',
        models.PROTECT,
        null=True,
        blank=True,
    )
    proposed = models.ForeignKey(
        CatalogProposal,
        models.PROTECT,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'combined_models'

    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=(
            'model_name__icontains',
            'brand_name__icontains',
        ),
    )
