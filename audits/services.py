from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from assets.models import Tblbrands, Tblcategories, Tblmodel, Tblassets, Tbllocations

from .models import (
    CombinedBrands,
    CombinedCategories,
    InventoryAudit,
    AuditLocation,
    AuditItem,
    CatalogProposal,
    AssetChangeProposal,
    AssetFieldChange,
    CombinedModels
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
    proposal_id=None
):

    entity_type = CatalogProposal.EntityType.MODEL
    proposed_name = (proposed_name or "").strip()

    if proposal_id:
        proposal = CatalogProposal.objects.get(pk=proposal_id)
        proposal.proposed_name=proposed_name
        proposal.proposed_model_number=proposed_model_number
        proposal.proposed_model_gtin=proposed_model_gtin
        proposal.proposed_brand=brand.existing
        proposal.proposed_category=category.existing
        proposal.brand_proposal=brand.proposed
        proposal.category_proposal=category.proposed
        proposal.discovered_in=discovered_in
        proposal.proposed_by=proposed_by
        proposal.status=CatalogProposal.Status.PROPOSED
        proposal.save()
        return proposal
    else:
        return CatalogProposal.objects.create(
            entity_type=entity_type,
            proposed_name=proposed_name,
            proposed_model_number=proposed_model_number,
            proposed_model_gtin=proposed_model_gtin,
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
    "locationid",
    "modelid",
    "customerassetnumber",
    "serialnumber",
}



@transaction.atomic
def review_catalog_proposal(*, proposal_id, reviewer, decision, replacement):
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
        _reject_catalog_proposal(proposal, reviewer, replacement)
        return proposal

    # Approve and apply, including any proposed dependencies.
    _apply_catalog_proposal(proposal, reviewer)

    return proposal

def _reject_catalog_proposal(proposal, reviewer, replacement):

    if replacement is None:
        raise ValidationError('A replacement candidate is required for rejecting a proposal')

    if proposal.entity_type == 'brand':
        combined_brand = CombinedBrands.objects.get(pk=replacement)
        dependent_proposals = CatalogProposal.objects.filter(
            brand_proposal=proposal.pk
        )

        dependent_proposals.update(
            proposed_brand=combined_brand.existing,
            brand_proposal=combined_brand.proposed
        )

    if proposal.entity_type == 'category':
        combined_brand = CombinedCategories.objects.get(pk=replacement)
        dependent_proposals = CatalogProposal.objects.filter(
            category_proposal=proposal.pk
        )

        dependent_proposals.update(
            proposed_category=combined_brand.existing,
            category_proposal=combined_brand.proposed
        )

    if proposal.entity_type == 'model':
        proposed_asset_changes = AssetFieldChange.objects.filter(
            field_name='modelid',
            proposed_value=proposal.pk
        )
        proposed_asset_changes.update(proposed_value=replacement.pk)
        

    proposal.status = CatalogProposal.Status.REJECTED
    proposal.reviewed_by = reviewer
    proposal.reviewed_at = timezone.now()
    proposal.save(update_fields=[
        "status",
        "reviewed_by",
        "reviewed_at",
    ])

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
            brandname=proposal.proposed_name,
        )
        proposal.approved_brand = brand

    elif proposal.entity_type == CatalogProposal.EntityType.CATEGORY:

        category, _ = Tblcategories.objects.get_or_create(
            categoryname=proposal.proposed_name,
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
            modelname=proposal.proposed_name,
            brandid=brand,
            categoryid=category,
            gtin=proposal.proposed_model_gtin
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
    proposed_by,
    reason,
    changes,
    audit_item=None,
    proposal=None,
):
    """
    changes example:
    {
        "location": 5,
        "model": 37,
        "serial_number": "SN-NEW-001",
    }

    Adapt the old-value extraction to your Asset model.
    """
    if audit_item:
        item = audit_item
    else:
        item = proposal.audit_item


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

    if proposal:
        proposal.changes.all().delete()

    else:
        proposal = AssetChangeProposal.objects.create(
            audit_item=item,
            reason=reason,
            proposed_by=proposed_by,
            status="pending",
        )
    

    for field_name, proposed_value in changes.items():
        if field_name == "locationid":
            if proposed_value is None:
                raise ValidationError("The proposed location does not exist.")

            proposed_value = {"value": proposed_value.pk}
            old_value = {"value": asset.locationid.pk}

        elif field_name == "modelid":
            if proposed_value is None:
                raise ValidationError("The proposed model or model proposal does not exist.")

            proposed_value = {
                "value": proposed_value.pk
            }

            current_model_id = asset.modelid.pk
            old_value = {"value" : CombinedModels.objects.filter(existing=current_model_id).first().pk}

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

    if proposal.status != "pending":
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
        proposal.changes.select_for_update().all()
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
            "locationid",
            "modelid",
            "customerassetnumber",
            "serialnumber",
        }:
            raise ValidationError(
                f"Unsupported asset field: {field_name}"
            )

        old_value = change.old_value
        proposed_value = change.proposed_value

        if field_name == "locationid":
            if asset.location_id != old_value.get("id"):
                raise ValidationError(
                    "The asset location has changed since the proposal "
                    "was created. Please review the changes again."
                )

            from assets.models import Tbllocations

            location = Tbllocations.objects.filter(
                pk=proposed_value.get("id")
            ).first()

            if location is None:
                raise ValidationError("The proposed location is invalid.")

            updates.append((change, field_name, location.pk))

        elif field_name == "modelid":

            current_combined_model_id = CombinedModels.objects.filter(
                existing=asset.modelid).first().pk
            if current_combined_model_id != old_value.get("id"):
                raise ValidationError(
                    "The asset model has changed since the proposal "
                    "was created. Please review the changes again."
                )


            combined_model = CombinedModels.objects.get(pk=proposed_value.get('id'))
            if combined_model.existing:
                model = Tblmodel.objects.filter(
                    pk=combined_model.existing.pk
                ).first()

                if model is None:
                    raise ValidationError(
                        "The selected official model does not exist."
                    )

            elif combined_model.proposed:
                catalog_proposal = CatalogProposal.objects.filter(
                    pk=combined_model.proposed.pk,
                    entity_type=CatalogProposal.EntityType.MODEL,
                    status=CatalogProposal.Status.APPLIED,
                ).first()

                if (
                    catalog_proposal is None
                    or catalog_proposal.approved_model_id is None
                ):
                    raise ValidationError(
                        "The proposed model must be approved"
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

    item.status = 'resolved'
    item.save(update_fields=['status'])

    return proposal


@transaction.atomic
def record_discovered_asset(
    *,
    proposed_by,
    changes,
    notes="",
    audit_location_id,
    proposal=None,
    audit_item=None,
):
    audit_location = AuditLocation.objects.select_related(
        "audit"
    ).get(pk=audit_location_id)


    if not audit_item: 
        audit_item = AuditItem.objects.create(
            audit=audit_location.audit,
            audit_location=audit_location,
            notes=notes,
            audited_by=proposed_by,
            status="pending",
        )


    if proposal:
        proposal.changes.all().delete()
    else:
        proposal = AssetChangeProposal.objects.create(
            audit_item=audit_item,
            reason='New asset found',
            proposed_by=proposed_by,
            status="pending",
        )
    
    AssetFieldChange.objects.create(
        proposal=proposal,
        field_name='locationid',
        old_value={'value':''},
        proposed_value={'value': audit_location.location.pk},
        decision="pending",
    )


    for field_name, proposed_value in changes.items():
        if field_name == "modelid":
            if proposed_value is None:
                raise ValidationError("The proposed model or model proposal does not exist.")

            proposed_value = {
                "value": proposed_value.pk
            }

            old_value = {"value" : ''}

        elif field_name == "customerid":
            if proposed_value is None:
                raise ValidationError("The proposed customer does not exist.")

            proposed_value = {
                "value": proposed_value.pk
            }

            old_value = {"value" : ''}
        else:
            # Scalar fields such as asset_number or serial_number.
            if not isinstance(proposed_value, str):
                raise ValidationError(
                    f"{field_name} must be provided as text."
                )

            old_value = {
                "value": '',
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
def review_new_asset_proposal(
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

    if proposal.status != "pending":
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
    if item.asset_id:
        raise ValidationError(
            "This audit item references an existing asset."
        )


    changes = list(
        proposal.changes.select_for_update().all()
    )

    if not changes:
        raise ValidationError("The proposal contains no changes.")

    has_customer_id = proposal.changes.filter(field_name='customerid').exists()
    # First validate every change. Do not mutate the asset until
    # all validation succeeds.
    updates = {}

    for change in changes:
        if change.decision != "pending":
            raise ValidationError(
                "All fields must still be pending review."
            )

        field_name = change.field_name

        if field_name not in {
            "locationid",
            "modelid",
            "customerassetnumber",
            "serialnumber",
            "customerid",
        }:
            raise ValidationError(
                f"Unsupported asset field: {field_name}"
            )

        proposed_value = change.proposed_value

        if field_name == "customerid":

            from assets.models import Tblcustomer

            customer = Tblcustomer.objects.filter(
                pk=proposed_value.get("value")
            ).first()

            if location is None:
                raise ValidationError("The proposed location is invalid.")

            updates[field_name] = customer

        elif field_name == "locationid":

            from assets.models import Tbllocations

            location = Tbllocations.objects.filter(
                pk=proposed_value.get("value")
            ).first()

            if location is None:
                raise ValidationError("The proposed location is invalid.")

            updates[field_name] = location

            if not has_customer_id:
                updates['customerid'] = location.customerid.pk


        elif field_name == "modelid":


            combined_model = CombinedModels.objects.get(pk=proposed_value.get('value'))
            if combined_model.existing:
                model = Tblmodel.objects.filter(
                    pk=combined_model.existing.pk
                ).first()

                if model is None:
                    raise ValidationError(
                        "The selected official model does not exist."
                    )

            elif combined_model.proposed:
                catalog_proposal = CatalogProposal.objects.filter(
                    pk=combined_model.proposed.pk,
                    entity_type=CatalogProposal.EntityType.MODEL,
                    status=CatalogProposal.Status.APPLIED,
                ).first()

                if (
                    catalog_proposal is None
                    or catalog_proposal.approved_model_id is None
                ):
                    raise ValidationError(
                        "The proposed model must be approved"
                        "before it can be assigned to an asset."
                    )

                model = catalog_proposal.approved_model

            else:
                raise ValidationError("Invalid model reference.")

            updates[field_name] = model

        else:

            value = proposed_value.get("value")

            if not isinstance(value, str):
                raise ValidationError(
                    f"The proposed {field_name} must be text."
                )

            updates[field_name] = value.strip()

    # All validation passed. Apply all changes.
    asset = Tblassets(**updates)
    asset.save()

    AssetFieldChange.objects.bulk_update(
        [change for change in changes],
        ["decision"],
    )

    proposal.status = "applied"
    proposal.reviewed_by = reviewer
    proposal.save(update_fields=["status", "reviewed_by"])

    item.status = 'resolved'
    item.save(update_fields=['status'])

    return proposal

