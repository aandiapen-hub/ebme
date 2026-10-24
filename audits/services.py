from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from assets.models import Tblbrands, Tblcategories, Tblmodel, Tblassets, Tbllocations

from .models import (
    InventoryAudit,
    AuditLocation,
    AuditItem,
    CatalogProposal,
    AssetChangeProposal,
    AssetFieldChange,
)


@transaction.atomic
def create_audit(*, name, created_by, locations, reference=None):
    """
    Create an audit campaign and assign its locations.

    locations must be an iterable of Location instances.
    """
    from assets.models import Tbllocations

    locations = list(locations)

    if not locations:
        raise ValidationError("An audit must include at least one location.")

    if not all(isinstance(location, Tbllocations) for location in locations):
        raise ValidationError("One or more locations are invalid.")

    audit = InventoryAudit.objects.create(
        name=name,
        created_by=created_by,
    )

    for location in locations:
            audit_location = AuditLocation.objects.create(
                audit=audit,
                location=location,
            )
            audit_location.save()

            # Find all assets currently assigned to this location.
            assets = Tblassets.objects.filter(locationid=location)

            # Create one audit item per asset.
            AuditItem.objects.bulk_create([
                AuditItem(
                    audit=audit,
                    audit_location=audit_location,
                    asset=asset,
                    status="pending",

                    # Snapshot the values at the start of the audit.
                    original_model=asset.modelid,

                    # Include other snapshots if your model defines them.
                    original_asset_number=asset.customerassetnumber,
                    original_serial_number=asset.serialnumber,
                )
                for asset in assets
            ])


    return audit

@transaction.atomic
def audit_item_verified(*, audit_item):
    audit_item.status = 'verified'
    audit_item.save()
    return audit_item

@transaction.atomic
def submit_catalog_proposal(
    *,
    entity_type,
    proposed_by,
    proposed_name,
    discovered_in=None,
    proposed_model_number=None,
    proposed_model_gtin=None,
    proposed_brand=None,
    proposed_category=None,
    brand_proposal=None,
    category_proposal=None,
):
    """
    Submit a proposed brand, category, or model.

    Existing catalogue objects and proposed catalogue objects remain
    separate until the proposal is applied.
    """
    allowed_types = {
        CatalogProposal.EntityType.BRAND,
        CatalogProposal.EntityType.CATEGORY,
        CatalogProposal.EntityType.MODEL,
    }

    if entity_type not in allowed_types:
        raise ValidationError("Unsupported catalogue proposal type.")

    proposed_name = (proposed_name or "").strip()

    if not proposed_name:
        raise ValidationError("A proposed name is required.")

    if entity_type == CatalogProposal.EntityType.BRAND:
        if any([
            proposed_brand,
            proposed_category,
            brand_proposal,
            category_proposal,
            proposed_model_number,
        ]):
            raise ValidationError(
                "A brand proposal cannot contain model or category dependencies."
            )

    elif entity_type == CatalogProposal.EntityType.CATEGORY:

        if any([
            proposed_category,
            category_proposal,
            brand_proposal,
            proposed_model_number,
        ]):
            raise ValidationError(
                "A category proposal contains invalid model dependencies."
            )


    elif entity_type == CatalogProposal.EntityType.MODEL:
        # A model needs both a brand and a category. Each can be either

        if bool(proposed_category) == bool(category_proposal):
            raise ValidationError(
                "Choose exactly one category source: existing or proposed."
            )

        if not (proposed_model_number or "").strip():
            raise ValidationError("A model number is required.")

        if proposed_model_gtin:
            if Tblmodel.objects.filter(gtin=gtin).exists():
                raise ValidationError(
                    "Model with this GTIN already exists"
                )


        if brand_proposal:
            if brand_proposal.entity_type != CatalogProposal.EntityType.BRAND:
                raise ValidationError("The brand dependency is invalid.")

            if brand_proposal.status == CatalogProposal.Status.REJECTED:
                raise ValidationError("The brand proposal was rejected.")

        if category_proposal:
            if category_proposal.entity_type != CatalogProposal.EntityType.CATEGORY:
                raise ValidationError("The category dependency is invalid.")

            if category_proposal.status == CatalogProposal.Status.REJECTED:
                raise ValidationError("The category proposal was rejected.")

    return CatalogProposal.objects.create(
        entity_type=entity_type,
        proposed_name=proposed_name,
        proposed_model_number=proposed_model_number,
        proposed_brand=proposed_brand,
        proposed_category=proposed_category,
        brand_proposal=brand_proposal,
        category_proposal=category_proposal,
        discovered_in=discovered_in,
        proposed_by=proposed_by,
        status=CatalogProposal.Status.PROPOSED,
    )

def submit_model_proposal(
    proposed_by,
    proposed_name,
    discovered_in,
    brand,
    category,
    proposed_model_number=None,
    proposed_model_gtin=None,
):

    entity_type = CatalogProposal.EntityType.MODEL
    proposed_name = (proposed_name or "").strip()

    return CatalogProposal.objects.create(
        entity_type=entity_type,
        proposed_name=proposed_name,
        proposed_model_number=proposed_model_number,
        proposed_brand=brand.existing,
        proposed_category=category.existing,
        brand_proposal=brand.proposed,
        category_proposal=category.proposed,
        discovered_in=discovered_in,
        proposed_by=proposed_by,
        status=CatalogProposal.Status.PROPOSED,
    )
    
def submit_brand_proposal(
    proposed_by,
    proposed_name,
    discovered_in,
):

    entity_type = CatalogProposal.EntityType.BRAND
    proposed_name = (proposed_name or "").strip()

    return CatalogProposal.objects.create(
        entity_type=entity_type,
        proposed_name=proposed_name,
        discovered_in=discovered_in,
        proposed_by=proposed_by,
        status=CatalogProposal.Status.PROPOSED,
    )

def submit_category_proposal(
    proposed_by,
    proposed_name,
    discovered_in,
):

    entity_type = CatalogProposal.EntityType.CATEGORY
    proposed_name = (proposed_name or "").strip()

    return CatalogProposal.objects.create(
        entity_type=entity_type,
        proposed_name=proposed_name,
        discovered_in=discovered_in,
        proposed_by=proposed_by,
        status=CatalogProposal.Status.PROPOSED,
    )

ALLOWED_ASSET_FIELDS = {
    "location",
    "model",
    "asset_number",
    "serial_number",
}



@transaction.atomic
def review_catalog_proposal(*, proposal_id, reviewer, decision):
    """
    One-step review for a catalogue proposal.

    decision:
        "approve" -> create/match official records and mark applied
        "reject"  -> reject without creating official records
    """

    if decision not in {"approve", "reject"}:
        raise ValidationError("Decision must be approve or reject.")

    proposal = CatalogProposal.objects.select_for_update().get(
        pk=proposal_id
    )

    if proposal.status != CatalogProposal.Status.PROPOSED:
        raise ValidationError("This proposal has already been reviewed.")

    if decision == "reject":
        proposal.status = CatalogProposal.Status.REJECTED
        proposal.reviewed_by = reviewer
        proposal.reviewed_at = timezone.now()
        proposal.save(update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
        ])
        return proposal

    # Approve and apply, including any proposed dependencies.
    _apply_catalog_proposal(proposal, reviewer)

    return proposal


def _apply_catalog_proposal(proposal, reviewer):
    """
    Internal helper. Must be called inside a transaction.
    Resolves proposed dependencies before creating the requested record.
    """

    proposal = CatalogProposal.objects.select_for_update().get(
        pk=proposal.pk
    )

    if proposal.status == CatalogProposal.Status.APPLIED:
        return proposal

    if proposal.status == CatalogProposal.Status.REJECTED:
        raise ValidationError(
            "A rejected proposal cannot be applied."
        )

    if proposal.entity_type == CatalogProposal.EntityType.BRAND:
        brand, _ = Tblbrands.objects.get_or_create(
            name=proposal.proposed_name,
        )
        proposal.approved_brand = brand

    elif proposal.entity_type == CatalogProposal.EntityType.CATEGORY:
        if proposal.brand_proposal_id:
            brand_proposal = _apply_catalog_proposal(
                proposal.brand_proposal,
                reviewer,
            )
            brand = brand_proposal.approved_brand
        else:
            brand = proposal.proposed_brand

        if brand is None:
            raise ValidationError(
                "The category requires a valid brand."
            )

        category, _ = Tblcategories.objects.get_or_create(
            name=proposal.proposed_name,
            brand=brand,
        )
        proposal.approved_category = category

    elif proposal.entity_type == CatalogProposal.EntityType.MODEL:
        if proposal.brand_proposal_id:
            brand_proposal = _apply_catalog_proposal(
                proposal.brand_proposal,
                reviewer,
            )
            brand = brand_proposal.approved_brand
        else:
            brand = proposal.proposed_brand

        if proposal.category_proposal_id:
            category_proposal = _apply_catalog_proposal(
                proposal.category_proposal,
                reviewer,
            )
            category = category_proposal.approved_category
        else:
            category = proposal.proposed_category

        if brand is None or category is None:
            raise ValidationError(
                "The model requires a valid brand and category."
            )

        model, _ = Tblmodel.objects.get_or_create(
            name=proposal.proposed_name,
            model_number=proposal.proposed_model_number,
            brand=brand,
            category=category,
        )
        proposal.approved_model = model

    else:
        raise ValidationError("Unsupported catalogue proposal type.")

    proposal.status = CatalogProposal.Status.APPLIED
    proposal.reviewed_by = reviewer
    proposal.reviewed_at = timezone.now()
    proposal.applied_at = timezone.now()

    proposal.save(update_fields=[
        "status",
        "reviewed_by",
        "reviewed_at",
        "applied_at",
        "approved_brand",
        "approved_category",
        "approved_model",
    ])

    return proposal

@transaction.atomic
def create_asset_change_proposal(
    *,
    audit_item_id,
    proposed_by,
    reason,
    changes,
):
    """
    changes example:
    {
        "location":  {"id": 5},
        "model":     {"source": "proposed", "id": 37},
        "serial_number": "SN-NEW-001",
    }

    Adapt the old-value extraction to your Asset model.
    """
    item = AuditItem.objects.select_related(
        "asset",
        "audit_location__location",
    ).get(pk=audit_item_id)

    if not item.asset_id:
        raise ValidationError(
            "This audit item represents a newly discovered asset."
        )

    if not changes:
        raise ValidationError("At least one proposed change is required.")

    invalid_fields = set(changes) - ALLOWED_ASSET_FIELDS
    if invalid_fields:
        raise ValidationError(
            f"Unsupported asset fields: {', '.join(sorted(invalid_fields))}"
        )

    asset = item.asset

    proposal = AssetChangeProposal.objects.create(
        audit_item=item,
        reason=reason,
        proposed_by=proposed_by,
        status="proposed",
    )

    for field_name, proposed_value in changes.items():
        if field_name == "location":
            proposed_id = proposed_value.get("id")
            if not proposed_id:
                raise ValidationError("A proposed location is required.")

            from locations.models import Location

            location = Tbllocations.objects.filter(pk=proposed_id).first()
            if location is None:
                raise ValidationError("The proposed location does not exist.")

            proposed_value = {"id": location.pk}
            old_value = {"id": asset.location_id}

        elif field_name == "model":
            source = proposed_value.get("source")
            model_id = proposed_value.get("id")

            if source == "existing":
                if not Tblmodel.objects.filter(pk=model_id).exists():
                    raise ValidationError("The selected model does not exist.")

            elif source == "proposed":
                catalog_proposal = CatalogProposal.objects.filter(
                    pk=model_id,
                    entity_type=CatalogProposal.EntityType.MODEL,
                    status__in=[
                        CatalogProposal.Status.PROPOSED,
                        CatalogProposal.Status.APPROVED,
                        CatalogProposal.Status.APPLIED,
                    ],
                ).first()

                if catalog_proposal is None:
                    raise ValidationError(
                        "The selected model proposal is unavailable."
                    )

            else:
                raise ValidationError("Invalid model source.")

            proposed_value = {
                "source": source,
                "id": model_id,
            }
            old_value = {"id": asset.model_id}

        else:
            # Scalar fields such as asset_number or serial_number.
            if not isinstance(proposed_value, str):
                raise ValidationError(
                    f"{field_name} must be provided as text."
                )

            old_value = {
                "value": getattr(asset, field_name),
            }
            proposed_value = {"value": proposed_value.strip()}

        AssetFieldChange.objects.create(
            proposal=proposal,
            field_name=field_name,
            old_value=old_value,
            proposed_value=proposed_value,
            decision="pending",
        )

    return proposal




@transaction.atomic
def review_asset_change_proposal(
    *,
    proposal_id,
    reviewer,
    decision,
):
    """
    One-step review for an asset change proposal.

    decision:
        "approve" -> validate and update the asset
        "reject"  -> reject without changing the asset
    """

    if decision not in {"approve", "reject"}:
        raise ValidationError("Decision must be approve or reject.")

    proposal = AssetChangeProposal.objects.select_for_update().get(
        pk=proposal_id
    )

    if proposal.status != "proposed":
        raise ValidationError(
            "This asset change proposal has already been reviewed."
        )

    if decision == "reject":
        proposal.status = "rejected"
        proposal.reviewed_by = reviewer
        proposal.save(update_fields=["status", "reviewed_by"])

        proposal.field_changes.filter(
            decision="pending"
        ).update(decision="rejected")

        return proposal

    item = proposal.audit_item
    if not item.asset_id:
        raise ValidationError(
            "This audit item does not reference an existing asset."
        )

    asset = Tblassets.objects.select_for_update().get(
        pk=item.asset_id
    )

    changes = list(
        proposal.field_changes.select_for_update().all()
    )

    if not changes:
        raise ValidationError("The proposal contains no changes.")

    # First validate every change. Do not mutate the asset until
    # all validation succeeds.
    updates = []

    for change in changes:
        if change.decision != "pending":
            raise ValidationError(
                "All fields must still be pending review."
            )

        field_name = change.field_name

        if field_name not in {
            "location",
            "model",
            "asset_number",
            "serial_number",
        }:
            raise ValidationError(
                f"Unsupported asset field: {field_name}"
            )

        old_value = change.old_value
        proposed_value = change.proposed_value

        if field_name == "location":
            if asset.location_id != old_value.get("id"):
                raise ValidationError(
                    "The asset location has changed since the proposal "
                    "was created. Please review the changes again."
                )

            from locations.models import Location

            location = Tbllocations.objects.filter(
                pk=proposed_value.get("id")
            ).first()

            if location is None:
                raise ValidationError("The proposed location is invalid.")

            updates.append((change, field_name, location))

        elif field_name == "model":
            if asset.model_id != old_value.get("id"):
                raise ValidationError(
                    "The asset model has changed since the proposal "
                    "was created. Please review the changes again."
                )

            source = proposed_value.get("source")
            reference_id = proposed_value.get("id")

            if source == "existing":
                model = Tblmodel.objects.filter(
                    pk=reference_id
                ).first()

                if model is None:
                    raise ValidationError(
                        "The selected official model does not exist."
                    )

            elif source == "proposed":
                catalog_proposal = CatalogProposal.objects.filter(
                    pk=reference_id,
                    entity_type=CatalogProposal.EntityType.MODEL,
                    status=CatalogProposal.Status.APPLIED,
                ).first()

                if (
                    catalog_proposal is None
                    or catalog_proposal.approved_model_id is None
                ):
                    raise ValidationError(
                        "The proposed model must be approved and applied "
                        "before it can be assigned to an asset."
                    )

                model = catalog_proposal.approved_model

            else:
                raise ValidationError("Invalid model reference.")

            updates.append((change, field_name, model))

        else:
            if getattr(asset, field_name) != old_value.get("value"):
                raise ValidationError(
                    f"{field_name} has changed since the proposal "
                    "was created. Please review the changes again."
                )

            value = proposed_value.get("value")

            if not isinstance(value, str):
                raise ValidationError(
                    f"The proposed {field_name} must be text."
                )

            updates.append((change, field_name, value.strip()))

    # All validation passed. Apply all changes.
    for change, field_name, value in updates:
        if field_name == "location":
            asset.location = value
        elif field_name == "model":
            asset.model = value
        else:
            setattr(asset, field_name, value)

        change.decision = "approved"

    asset.save()

    AssetFieldChange.objects.bulk_update(
        [change for change, _, _ in updates],
        ["decision"],
    )

    proposal.status = "applied"
    proposal.reviewed_by = reviewer
    proposal.save(update_fields=["status", "reviewed_by"])

    return proposal


@transaction.atomic
def record_discovered_asset(
    *,
    audit_location_id,
    audited_by,
    observed_model=None,
    observed_model_proposal=None,
    notes="",
):
    audit_location = AuditLocation.objects.select_related(
        "audit"
    ).get(pk=audit_location_id)

    if bool(observed_model) and bool(observed_model_proposal):
        raise ValidationError(
            "Select an existing model or a proposed model, not both."
        )

    return AuditItem.objects.create(
        audit=audit_location.audit,
        audit_location=audit_location,
        asset=None,
        observed_model=observed_model,
        observed_model_proposal=observed_model_proposal,
        notes=notes,
        audited_by=audited_by,
        status="pending",
    )
