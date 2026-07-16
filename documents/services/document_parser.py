import biip
from django.db.models import Q
from assets.models import (
    AssetView,
    Tblassets,
    Tblmodel,
    JobView,
    Tblbrands,
    Tblcategories,
)
from cap_project.models import CommissionRequest

from parts.models import Tblpartslist
from documents.models import TempUploadGroup, DocumentTypes
from procurement.models import TblPurchaseOrder, TblDeliveries


def asset_data_builder(
    gtin=None,
    add_gtin=False,
    asset_id=None,
    assets=None,
    serial=None,
    prod_date=None,
    asset_no=None,
    too_many_assets=False,
    create_asset=False,
    jobs=None,
    too_many_jobs=False,
    model_id=None,
    duplicatable_models=None,
    models_without_gtin=None,
    model_name_options=None,
    brand_name_options=None,
    brand_ids=None,
    category_name_options=None,
    category_ids=None,
    part_id=None,
    part_number=None,
    part_short_name=None,
    part_description=None,
    parts_without_gtin=None,
    suggested_new_part_names=None,
    ordernumber=None,
    locationid=None,
    customerid=None,
    unitprice=None,
):
    return {
        "gtin": {
            "value": gtin,
            "add_gtin": add_gtin,
        }, "asset": {
            "asset_id": asset_id,
            "serialnumber": serial,
            "customerassetnumber": asset_no,
            "modelid": model_id,
            "assets": assets or [],
            "prod_date": prod_date,
            "create_asset": create_asset,
            "too_many_assets": too_many_assets,
            "ordernumber":ordernumber,
            "locationid":locationid,
            "customerid":customerid,
            "unitprice":unitprice,
        },
        "job": {
            "jobs": jobs or [],
            "too_many_jobs": too_many_jobs,
        },
        "model": {
            "gtin": gtin,
            "modelname": model_name_options or [],
            "brandname": brand_name_options or [],
            "brand_ids": brand_ids or [],
            "categoryname": category_name_options or [],
            "category_ids": category_ids,
            "model_id": model_id,
            "duplicatable_models": duplicatable_models or [],
            "models_without_gtin": models_without_gtin or [],
        },
        "part": {
            "gtin": gtin,
            "part_id": part_id,
            "suggested_new_name": suggested_new_part_names or [],
            "part_number": part_number,
            "short_name": part_short_name,
            "description": part_description,
            "parts": parts_without_gtin,
        },
        "brand": {
            "brand_options": brand_name_options or [],
            "brand_ids": brand_ids,
        },
        "category": {
            "category_options": category_name_options or [],
            "category_ids": category_ids,
        },
    }


def job_data_builder(
    gtin=None,
    add_gtin=False,
    asset_id=None,
    assets=None,
    serial=None,
    asset_no=None,
    create_asset=False,
    jobs=None,
    model_id=None,
    model_name_options=None,
    brand_name_options=None,
    brand_ids=None,
    job_ref=None,
    start_date=None,
    end_date=None,
    cal_date=None,
    workdone=None,
    jobtypeid=None,
    jobstatusid=None,
    create_job=False,
):
    return {
        "gtin": {
            "value": gtin,
            "add_gtin": add_gtin,
        },
        "asset": {
            "asset_id": asset_id,
            "serial": serial,
            "asset_no": asset_no,
            "assets": assets or [],
            "create_asset": create_asset,
        },
        "job": {
            "assetid": asset_id,
            "jobs": jobs or [],
            "job_ref": job_ref,
            "jobstartdate": start_date,
            "jobenddate": end_date,
            "workdone": workdone,
            "jobtypeid": jobtypeid,
            "jobstatusid": jobstatusid,
            "create_job": create_job,
        },
        "model": {
            "model_id": model_id,
            "name_options": model_name_options or [],
        },
        "brand": {
            "brand_options": brand_name_options or [],
            "brand_ids": brand_ids,
        },
    }


def delivery_data_builder(
    delivery_note_number=None,
    delivery_ids=None,
    create_delivery=False,
    po_id=None,
    delivery_date=None,
    items=None,
):
    return {
        "delivery": {
            "delivery_note_number": delivery_note_number,
            "delivery_ids": delivery_ids,
            "create_delivery": create_delivery,
            "po": po_id,
            "delivery_date": delivery_date,
            "items_list": items
        }
    }


def parse_gs1code(scanned_code=None):
    gs1_codes = [scanned_code]

    output = {}
    non_gs1_codes = []

    for code in gs1_codes:
        # ignore internal codes
        parsed_gs1 = biip.parse(code)

        if parsed_gs1.gs1_message is None:
            non_gs1_codes.append(code)
            continue

        for es in parsed_gs1.gs1_message.element_strings:
            if es.ai.ai == '91' and len(parsed_gs1.gs1_message.element_strings)==1:
                output.update({'com_request': es.value})
                break 
            if es.ai.data_title == 'INTERNAL':
                non_gs1_codes.append(code)
                continue
            output.update({es.ai.data_title: es.value})

            if es.ai.data_title == "GIAI":
                output["ASSET_NO"] = es.value[-7:]

    output['non_gs1_codes'] = non_gs1_codes
    return output


def match_options(qs, fieldname, options):
    search_terms = []
    for item in options:
        search_terms += item.split()
    search_term = [term for term in search_terms if len(term) > 3]
    q_filter = Q()
    search_criteria = f"{fieldname}__icontains"
    for term in search_term:
        q_filter |= Q(**{search_criteria: term})

    filtered = qs.filter(q_filter).values_list("pk", fieldname)
    qs_ids = []
    qs_names = set()

    for pk, name in filtered:
        qs_ids.append(pk)
        qs_names.add(name)

    options = [option for option in options if option not in qs_names]

    return list(qs_ids), options


def find_asset_by_asset_no(asset_no):
    if not asset_no:
        return None

    return AssetView.objects.filter(
        customerassetnumber=asset_no
    ).prefetch_related("jobs").first()


def find_asset_by_serial_and_model(serial, model):
    if not (serial and model):
        return None

    return Tblassets.objects.filter(
        serialnumber__icontains=serial, modelid=model
    ).prefetch_related("jobs").first()


def resolve_gtin(gtin):
    if not gtin:
        return None, None, None

    model = Tblmodel.objects.filter(gtin=gtin).first()
    part = Tblpartslist.objects.filter(gtin=gtin).first()

    add_gtin = not (model or part)

    return model, part, add_gtin


def find_partial_asset_matches(serial):

    assets_qs = AssetView.objects.filter(serialnumber__icontains=serial)

    assets = list(assets_qs.values_list("pk", flat=True))
    too_many_assets = len(assets) > 10

    if not assets:
        return {
            "assets": [],
            "too_many_assets": False,
            "models_with_gtin": [],
            "models_without_gtin": [],
            "jobs": []
        }

    model_ids = list(assets_qs.values_list("modelid", flat=True))

    models_with_gtin = list(
        Tblmodel.objects.filter(
            modelid__in=model_ids,
            gtin__isnull=False
        ).values_list("pk", flat=True)
    )

    models_without_gtin = list(
        Tblmodel.objects.filter(
            modelid__in=model_ids,
            gtin__isnull=True
        ).values_list("pk", flat=True)
    )

    jobs = JobView.objects.filter(assetid__in=assets).values_list('pk', flat=True)

    return {
        "assets": assets,
        "too_many_assets": too_many_assets,
        "models_with_gtin": models_with_gtin,
        "models_without_gtin": models_without_gtin,
        'jobs': jobs,
    }


def gs1_resolver(parsed_data):
    asset_no = parsed_data.get("ASSET_NO")
    gtin = parsed_data.get("GTIN")
    serial = parsed_data.get("SERIAL")
    prod_date = parsed_data.get("PROD DATE")

    # defaults
    known_model = None
    known_part = None

    asset_id = None
    assets = []
    jobs = []
    create_asset = False
    too_many_assets = False

    model_id = None
    models_with_gtin = []
    models_without_gtin = []

    part_id = None
    add_gtin = False

    # -------------------------
    # 1. Asset lookup (strongest)
    # -------------------------
    asset = find_asset_by_asset_no(asset_no)
    if asset:
        jobs = list(asset.jobs.all().values_list("pk", flat=True))
        return asset_data_builder(
            gtin=gtin,
            asset_id=asset.pk,
            jobs=jobs,
        )
    create_asset = bool(asset)

    # -------------------------
    # 2. GTIN lookup
    # -------------------------
    known_model, known_part, add_gtin = resolve_gtin(gtin)
    model_id = known_model.pk if known_model else None
    part_id = known_part.pk if known_part else None

    # -------------------------
    # 3. Exact asset match
    # -------------------------

    asset = find_asset_by_serial_and_model(serial, known_model)
    if asset:
        jobs = list(asset.jobs.values_list("pk", flat=True))
        return asset_data_builder(
            gtin=gtin,
            asset_id=asset.pk,
            model_id=model_id,
            jobs=jobs,
        )
    create_asset = not bool(asset) or bool(serial and known_model)

    # -------------------------
    # 4. Partial match
    # -------------------------
    if serial and not known_model:
        result = find_partial_asset_matches(serial)

        assets = result["assets"]
        too_many_assets = result["too_many_assets"]
        models_with_gtin = result["models_with_gtin"]
        models_without_gtin = result["models_without_gtin"]
        jobs += result['jobs']

        create_asset = True

    # -------------------------
    # 5. Model
    # -------------------------
    model_name_options = parsed_data.get("model_name_options", [])

    # -------------------------
    # 6. Brand
    # -------------------------
    #
    brand_name_options = parsed_data.get("brand_name_options", None)
    brand_ids = []
    if brand_name_options:
        brand_ids, brand_name_options = match_options(
            qs=Tblbrands.objects.all(),
            fieldname="brandname",
            options=brand_name_options,
        )
    brand_ids += parsed_data.get("brand_id", [])

    # -------------------------
    # 7. Category
    # -------------------------
    category_name_options = parsed_data.get("category_name_options", None)
    category_ids = []
    if category_name_options:
        category_ids, category_name_options = match_options(
            qs=Tblcategories.objects.all(),
            fieldname="categoryname",
            options=category_name_options,
        )

    category_name_options = parsed_data.get("category_name_options", None)

    # -------------------------
    # 8. Spare Part 
    # -------------------------
    part_number = parsed_data.get("model")
    part_short_name = parsed_data.get("description")

    # -------------------------
    # 9. Commission Requset 
    # -------------------------
    com_request_code = parsed_data.get('com_request')
    ordernumber = None
    locationid = None
    customerid = None
    unitprice = None
    if com_request_code:
        com_request = CommissionRequest.objects.filter(code=com_request_code).first()
        if com_request:
            ordernumber = com_request.orderno
            locationid = com_request.locationid
            customerid = com_request.customerid
            unitprice = com_request.unitprice

    part_number = parsed_data.get("model")

    part_short_name = parsed_data.get("description")
    # -------------------------
    # FINAL OUTPUT
    # -------------------------
    return asset_data_builder(
        gtin=gtin,
        add_gtin=add_gtin,
        asset_id=asset_id,
        assets=assets,
        asset_no=asset_no,
        serial=serial,
        prod_date=prod_date,
        create_asset=create_asset,
        too_many_assets=too_many_assets,
        jobs=jobs,
        model_id=model_id,
        duplicatable_models=models_with_gtin,
        models_without_gtin=models_without_gtin,
        model_name_options=model_name_options,
        brand_name_options=brand_name_options,
        brand_ids=brand_ids,
        category_name_options=category_name_options,
        category_ids=category_ids,
        part_id=part_id,
        part_number=part_number,
        part_short_name=part_short_name,
        ordernumber=ordernumber,
        locationid=locationid,
        customerid=customerid,
        unitprice=unitprice,
    )


def job_resolver(parsed_data):
    asset_no = parsed_data.get("ASSET_NO")
    gtin = parsed_data.get("GTIN")
    serial = parsed_data.get("SERIAL")

    asset_id = None
    assets = []
    jobs = []

    model_id = None

    add_gtin = False

    cal_date = parsed_data.get("cal_date", None)
    end_date = parsed_data.get("end_date", None)
    start_date = parsed_data.get("start_date", None)
    workdone = parsed_data.get("workdone", None)
    jobtypeid = parsed_data.get("jobtypeid", None)
    jobstatusid = parsed_data.get("jobstatusid", None)
    # -------------------------
    # 1. Asset lookup (strongest)
    # -------------------------
    asset = find_asset_by_asset_no(asset_no)
    if asset:
        jobs = list(asset.jobs.values_list("pk", flat=True))
    create_asset = bool(asset)

    # -------------------------
    # 2. GTIN lookup
    # -------------------------
    known_model, known_part, add_gtin = resolve_gtin(gtin)
    model_id = known_model.pk if known_model else None

    # -------------------------
    # 3. Exact asset match
    # -------------------------

    asset = find_asset_by_serial_and_model(serial, known_model)
    if asset:
        jobs = list(asset.jobs.values_list("pk", flat=True))
        return job_data_builder(
            gtin=gtin,
            asset_id=asset.pk,
            model_id=model_id,
            jobs=jobs,
        )
    create_asset = not bool(asset) or bool(serial and known_model)

    # -------------------------
    # 4. Partial match
    # -------------------------
    if serial and not known_model:
        result = find_partial_asset_matches(serial)
        assets = result["assets"]
        create_asset = True

        if asset_id is None and assets:
            asset_id = assets[0]
        jobs = list(JobView.objects.filter(assetid__in=assets).values_list("pk", flat=True))

    # -------------------------
    # 6. Job
    # -------------------------
    create_job = any([
        parsed_data.get("cal_date", None),
        parsed_data.get("end_date", None),
        parsed_data.get("start_date", None),
        parsed_data.get("workdone", None),
        parsed_data.get("jobtypeid", None),
        parsed_data.get("jobstatusid", None),
    ])
    # -------------------------
    # FINAL OUTPUT
    # -------------------------
    return job_data_builder(
        gtin=gtin,
        add_gtin=add_gtin,
        asset_id=asset_id,
        assets=assets,
        asset_no=asset_no,
        serial=serial,
        create_asset=create_asset,
        jobs=jobs,
        model_id=model_id,
        create_job=create_job,
        start_date=start_date,
        end_date=end_date,
        cal_date=cal_date,
        workdone=workdone,
        jobtypeid=jobtypeid,
        jobstatusid=jobstatusid,
    )


def delivery_resolver(parsed_data):
    po_number = parsed_data.get('purchase_order', None)
    delivery_note_number_options = parsed_data.get('delivery_note_number_options', None)
    delivery_date = parsed_data.get('delivery_date', None)
    delivery_items = parsed_data.get('delivery_items', None)

    po_id = None
    existing_deliveries = None
    create_delivery = False

    if po_number:
        print('po_number', po_number, type(po_number))
        po = TblPurchaseOrder.objects.filter(po_id__in=po_number).first()
        if po:
            po_id = po.pk


    if po_id and delivery_note_number_options:
        create_delivery = True

    if delivery_note_number_options:
        existing_deliveries = list(
                TblDeliveries.objects.filter(
                    delivery_note_number__in=delivery_note_number_options
                ).values_list('pk', flat=True)
        )

    delivery_items = {item['part_number']: item['quantity'] for item in delivery_items}

    return delivery_data_builder(
        delivery_note_number=delivery_note_number_options,
        delivery_ids=existing_deliveries,
        create_delivery=create_delivery,
        po_id=po_id,
        delivery_date=delivery_date,
        items=delivery_items
    )


RESOLVER_MAP = {
    DocumentTypes.ASSET_DATA.value: gs1_resolver,
    DocumentTypes.SERVICE_REPORT.value: job_resolver,
    DocumentTypes.DELIVERY_NOTE.value: delivery_resolver,
}


def temp_group_resolver(group_id):
    group = TempUploadGroup.objects.filter(pk=group_id).first()
    if not group:
        return

    data = group.extracted_json.get("merged_gs1_ai", None)
    if data is None:
        data = group.extracted_json.get("merged_parsed_barcode", {}).get('values',{})

    resolver = RESOLVER_MAP.get(group.document_type_id, gs1_resolver)
    if data and resolver:
        resolved_data = resolver(data)
        group.extracted_json.update({"resolved": resolved_data})
        group.save(update_fields=["extracted_json"])


def rapid_gs1_resolver(barcode):
    parsed_barcode = parse_gs1code(scanned_code = barcode)
    return gs1_resolver(parsed_barcode)


