import biip
from PIL import Image
import zxingcpp
from django.core.exceptions import ValidationError
from django.db.models import Q
from dataclasses import dataclass
from collections import defaultdict
import json

from assets.models import (
    AssetView,
    Tblassets,
    Tblmodel,
    JobView,
    Tblbrands,
    Tblcategories,
)

from parts.models import Tblpartslist
from documents.models import TempUploadGroup, DocumentTypes


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
    models_with_gtin=None,
    models_without_gtin=None,
    model_name_options=None,
    brand_name_options=None,
    brand_ids=None,
    category_name_options=None,
    category_ids=None,
    part_id=None,
    suggested_new_part_names=None,
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
            "prod_date": prod_date,
            "too_many_assets": too_many_assets,
        },
        "job": {
            "jobs": jobs or [],
            "too_many_jobs": too_many_jobs,
        },
        "model": {
            "model_id": model_id,
            "models_with_gtin": models_with_gtin or [],
            "models_without_gtin": models_without_gtin or [],
            "name_options": model_name_options or [],
        },
        "part": {
            "part_id": part_id,
            "suggested_new_name": suggested_new_part_names or [],
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


def quick_scan_barcode(image):
    img = Image.open(image)
    barcodes = zxingcpp.read_barcodes(img, text_mode=zxingcpp.Plain)
    if len(barcodes) == 0:
        raise ValidationError({"file": "Could not find any barcode"})

    gs1_codes = [code for code in barcodes if code.content_type == zxingcpp.GS1]
    return gs1_codes


def parse_gs1code(file=None, scanned_code=None):
    if file:
        # scan image for barcode and get a list of test
        gs1_codes = [code.text for code in quick_scan_barcode(file)]
        print("code to be parsed from file", gs1_codes)
    else:
        gs1_codes = [scanned_code]
        print("code to be parsed from text given", gs1_codes)

    output = {}

    for code in gs1_codes:
        # ignore internal codes
        if code.startswith("9"):
            return None
        parsed_gs1 = biip.parse(code)

        if parsed_gs1.gs1_message is None:
            raise ValidationError({"__all__": "Invalid gs1 code"})

        for es in parsed_gs1.gs1_message.element_strings:
            if es.ai.data_title not in output:
                output[es.ai.data_title] = es.value
            else:
                raise ValidationError(
                    {"__all__": "Multiple GS1 barcode of the same type scanned"}
                )

            if es.ai.data_title == "GIAI":
                output["ASSET_NO"] = es.value[-7:]

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
        assetid=asset_no
    ).prefetch_related("jobs").first()


def find_asset_by_serial_and_model(serial, model):
    if not (serial and model):
        return None

    return AssetView.objects.filter(
        serialnumber=serial, modelid=model
    ).prefetch_related("jobs") .first()


def resolve_gtin(gtin):
    if not gtin:
        return None, None, None

    model = Tblmodel.objects.filter(gtin=gtin).first()
    part = Tblpartslist.objects.filter(gtin=gtin).first()

    add_gtin = not (model or part)

    return model, part, add_gtin


def find_partial_asset_matches(serial):
    if not serial:
        return {
            "assets": [],
            "too_many_assets": False,
            "models_with_gtin": [],
            "models_without_gtin": [],
            "jobs": [],
        }

    assets_qs = AssetView.objects.filter(serialnumber__icontains=serial)

    assets = list(assets_qs.values_list("pk", flat=True))
    too_many_assets = len(assets) > 10

    if not assets:
        return {
            "assets": [],
            "too_many_assets": False,
            "models_with_gtin": [],
            "models_without_gtin": [],
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
        if asset:
            jobs = list(asset.jobs.values_list("id", flat=True))
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
    if brand_name_options is not None:
        brand_ids, brand_name_options = match_options(
            qs=Tblbrands.objects.all(),
            fieldname="brandname",
            options=brand_name_options,
        )
    brand_ids += parsed_data.get("brand_id", [])

    # -------------------------
    # 7. Category
    # -------------------------
    category_name_options = parsed_data.get("category_name_options", [])
    category_ids = []
    if category_name_options is not None:
        category_ids, category_name_options = match_options(
            qs=Tblcategories.objects.all(),
            fieldname="categoryname",
            options=category_name_options,
        )

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
        models_with_gtin=models_with_gtin,
        models_without_gtin=models_without_gtin,
        model_name_options=model_name_options,
        brand_name_options=brand_name_options,
        brand_ids=brand_ids,
        category_name_options=category_name_options,
        category_ids=category_ids,
        part_id=part_id,
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
        if asset:
            jobs = list(asset.jobs.values_list("id", flat=True))
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

        if asset_id is None:
            asset_id = assets[0]
        jobs = list(JobView.objects.filter(assetid__in=assets).values_list("pk", flat=True))

    # -------------------------
    # 5. Model
    # -------------------------
    model_name_options = parsed_data.get("model_name_options", [])

    # -------------------------
    # 6. Brand
    # -------------------------

    brand_name_options = parsed_data.get("brand_name_options", None)
    brand_ids = []
    if brand_name_options is not None:
        brand_ids, brand_name_options = match_options(
            qs=Tblbrands.objects.all(),
            fieldname="brandname",
            options=brand_name_options,
        )
    brand_ids += parsed_data.get("brand_id", [])

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
        model_name_options=model_name_options,
        brand_name_options=brand_name_options,
        brand_ids=brand_ids,
        create_job=create_job,
        start_date=start_date,
        end_date=end_date,
        cal_date=cal_date,
        workdone=workdone,
        jobtypeid=jobtypeid,
        jobstatusid=jobstatusid,
    )

RESOLVER_MAP = {
    DocumentTypes.ASSET_DATA.value: gs1_resolver,
    DocumentTypes.SERVICE_REPORT.value: job_resolver,
}

def temp_group_resolver(group_id):
    group = TempUploadGroup.objects.get(pk=group_id)
    merged_parsed_data = group.extracted_json.get("merged_gs1_ai", None)
    resolver = RESOLVER_MAP.get(group.document_type_id, None)
    if merged_parsed_data and resolver:
        group.extracted_json.update({"resolved": resolver(merged_parsed_data)})
        group.save(update_fields=["extracted_json"])


def non_gs1_result(data):
    max_result_count = 10
    output = {}
    output["search_term"] = data
    asset_filter = Q(serialnumber__icontains=data) | Q(assetid__icontains=data)
    assets = AssetView.objects.filter(asset_filter).order_by(
        "brandid", "modelid", "serialnumber"
    )
    if assets.count() <= max_result_count:
        output["assets"] = assets
    if assets.count() > max_result_count:
        output["too_many_assets"] = True

    job_filter = Q(jobid__icontains=data)
    jobs = JobView.objects.filter(job_filter).order_by("enddate")

    if assets.count() == 1:
        jobs = assets.first().jobs.all()
    if jobs.count() <= max_result_count:
        output["jobs"] = jobs
    if jobs.count() > max_result_count:
        output["too_many_jobs"] = True

    return output


def process_barcode(file=None, scanned_code=None):
    decoded_info = {}
    try:
        decoded_info = parse_gs1code(file=file, scanned_code=scanned_code)

    except ValidationError:
        output = non_gs1_result(scanned_code)
        output["search_term"] = scanned_code
        return output
    else:
        output = gs1_resolver(decoded_info)
        output["search_term"] = (
            f"{output.get('gs1').get('SERIAL', '')} {output.get('gs1').get('ASSET_NO', '')}"
        )
        return output


@dataclass
class Action:
    key: str
    label: str
    enabled: Tblmodel
    route_name: str
    pk: str | None = None
    payload: dict | None = None


class ActionResolver:
    def __init__(self,temp_group_pk, data):
        self.actions = defaultdict(list)
        self.temp_group_pk = str(temp_group_pk)
        self.data = data
        print(self.data)

    def resolve(self):
        self.gtin_actions()
        self.model_actions()
        self.asset_actions()
        self.service_report_actions()

        for action_list in self.actions.values():
            for action in action_list:
                action.payload_json = json.dumps(action.payload)
        return dict(self.actions)

    # -------------
    # GTIN Actions
    # -------------

    def gtin_actions(self):
        if self.data.get("gtin", {}).get("add_gtin"):
            # create model
            self.actions["gtin"].append(
                Action(
                    key="create_model",
                    label="Create Model",
                    enabled=True,
                    route_name="model_information:create_model",
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "gtin": self.data.get("gtin").get("value"),
                        "modelname": self.data.get("model").get("name_options"),
                        "brandname": self.data.get("brand").get("brand_options"),
                        "brandid": self.data.get("brand").get("brand_ids"),
                        "categoryname": self.data.get("model").get(
                            "category_options"
                        ),
                        "categoryid": self.data.get("category").get("category_ids"),
                    },
                )
            )
            # create spare parts
            self.actions["gtin"].append(
                Action(
                    key="create_spare_part",
                    label="Create Spare Part",
                    enabled=True,
                    route_name="parts:create_part",
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "gtin": self.data.get("gtin").get("value")
                    },
                )
            )

    # -------------
    # Model Actions
    # -------------
    def model_actions(self):
        # update existing model
        models_without_gtin = self.data.get("model", {}).get("models_without_gtin", {})
        if models_without_gtin is None:
            for model in models_without_gtin:
                self.actions["model"].append(
                    Action(
                        key=f"update_model_{model}",
                        label=f"Update {model}",
                        enabled=True,
                        route_name="model_information:update_model",
                        pk=model,
                        payload={
                            "temp_group_pk": self.temp_group_pk,
                            "gtin": self.data.get("gtin").get("value"),
                        },
                    )
                )

        models_with_gtin = self.data.get("model", {}).get("models_with_gtin", {})
        if models_with_gtin is None:
            for model in models_with_gtin:
                self.actions["model"].append(
                    Action(
                        key=f"update_model_{model}",
                        label=f"Update {model}",
                        enabled=True,
                        route_name="model_information:update_model",
                        pk=model,
                        payload={
                            "temp_group_pk": self.temp_group_pk,
                        },
                    )
                )

    # -------------
    # Asset Actions
    # -------------

    def asset_actions(self):
        # Open Asset
        asset_id = self.data.get("asset", {}).get("asset_id")
        if asset_id is not None:
            self.actions["asset"].append(
                Action(
                    key="open_asset",
                    label="Open Asset",
                    enabled=True,
                    route_name="assets:view_asset",
                    pk=asset_id,
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "pk": asset_id,
                    },
                )
            )

        # Open partially matched Asset
        asset_ids = self.data.get("asset", {}).get("assets")
        if asset_id:
            asset_ids.remove(asset_id)
        for asset in asset_ids:
            self.actions["asset"].append(
                Action(
                    key="open_partially_matched_assets",
                    label=f"{repr(asset)}",
                    enabled=True,
                    route_name="assets:view_asset",
                    pk=asset,
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                    },
                )
            )

        # Create Asset
        if self.data.get("asset", {}).get("create_asset"):
            self.actions["asset"].append(
                Action(
                    key="create_asset",
                    label="Create Asset",
                    enabled=True,
                    route_name="assets:create_asset",
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "gtin": self.data.get("gtin", {}).get("value"),
                        "modelid": self.data.get("model", {}).get("model_id"),
                        "serialnumber": self.data.get("asset", {}).get("serial"),
                        "customerassetnumber": self.data.get("asset", {}).get(
                            "asset_no"
                        ),
                        "prod_date": self.data.get("asset", {}).get("prod_date"),
                    },
                )
            )

    # -------------
    # Service Report Actions
    # -------------
    def service_report_actions(self):
        # Log Service Report
        if self.data.get('job', {}).get("create_job", None):
            self.actions["job"].append(
                Action(
                    key="log_service_report",
                    label="Log Report",
                    enabled=True,
                    route_name="documents:log_service_report",
                    pk=self.temp_group_pk,
                    payload={
                    },
                )
            )


def get_assets_from_resolved_data(data):
    asset_ids = data.get('asset', {}).get('assets', [])
    return Tblassets.objects.filter(pk__in=asset_ids)

