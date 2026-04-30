import biip
from PIL import Image
import zxingcpp
from django.core.exceptions import ValidationError
from django.db.models import Q
from dataclasses import dataclass
from collections import defaultdict
import json

from assets.models import AssetView, Tblmodel, JobView, Tblbrands, Tblcategories

from parts.models import Tblpartslist
from documents.models import TempUploadGroup


def data_builder(
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
    print("search_term", search_terms)
    q_filter = Q()
    search_criteria = f"{fieldname}__icontains"
    for term in search_term:
        q_filter |= Q(**{search_criteria: term})
    pks = list(qs.filter(q_filter).values_list("pk", flat=True))
    print("matched pks", pks)
    return pks


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
    if asset_no:
        asset = (
            AssetView.objects.filter(assetid=asset_no).prefetch_related("jobs").first()
        )

        if asset:
            asset_id = asset.id
            jobs = list(asset.jobs.values_list("id", flat=True))
            return data_builder(
                parsed_data=parsed_data,
                gtin=gtin,
                asset_id=asset_id,
                jobs=jobs,
            )
        else:
            create_asset = True

    # -------------------------
    # 2. GTIN lookup
    # -------------------------
    if gtin:
        known_model = Tblmodel.objects.filter(gtin=gtin).first()
        known_part = Tblpartslist.objects.filter(gtin=gtin).first()

        if known_model:
            model_id = known_model.pk

        if known_part:
            part_id = known_part.pk

        if not known_model and not known_part:
            add_gtin = True

    # -------------------------
    # 3. Exact asset match
    # -------------------------
    if serial and known_model:
        asset = (
            AssetView.objects.filter(serialnumber=serial, modelid=known_model)
            .prefetch_related("jobs")
            .first()
        )

        if asset:
            asset_id = asset.id
            jobs = list(asset.jobs.values_list("pk", flat=True))
            return data_builder(
                parsed_data=parsed_data,
                gtin=gtin,
                asset_id=asset_id,
                model_id=model_id,
                jobs=jobs,
            )
        else:
            create_asset = True

    # -------------------------
    # 4. Partial match
    # -------------------------
    if serial and not known_model:
        assets_qs = AssetView.objects.filter(serialnumber__icontains=serial)

        assets = list(assets_qs.values_list("pk", flat=True))
        too_many_assets = len(assets) > 5

        if assets:
            model_ids = list(assets_qs.values_list("modelid", flat=True))

            models_with_gtin = list(
                Tblmodel.objects.filter(
                    modelid__in=model_ids, gtin__isnull=False
                ).values_list("id", flat=True)
            )

            models_without_gtin = list(
                Tblmodel.objects.filter(
                    modelid__in=model_ids, gtin__isnull=True
                ).values_list("id", flat=True)
            )

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
        brand_ids = match_options(
            qs=Tblbrands.objects.all(),
            fieldname="brandname",
            options=brand_name_options,
        )

    # -------------------------
    # 7. Category
    # -------------------------
    category_name_options = parsed_data.get("category_name_options", [])
    category_ids = []
    if category_name_options is not None:
        category_ids = match_options(
            qs=Tblcategories.objects.all(),
            fieldname="categoryname",
            options=category_name_options,
        )

    # -------------------------
    # FINAL OUTPUT
    # -------------------------
    return data_builder(
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


def temp_group_resolver(group_id):
    group = TempUploadGroup.objects.get(pk=group_id)
    merged_parsed_data = group.extracted_json.get("merged_gs1_ai", None)
    if merged_parsed_data is not None:
        group.extracted_json.update({"resolved": gs1_resolver(merged_parsed_data)})
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
                        "brand_options": self.data.get("brand").get("brand_options"),
                        "brandid": self.data.get("brand").get("brand_ids"),
                        "category_options": self.data.get("model").get(
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
                        payload={
                            "temp_group_pk": self.temp_group_pk,
                            "gtin": self.data.get("gtin").get("value"),
                            "pk": model,
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
                        payload={
                            "temp_group_pk": self.temp_group_pk,
                            "pk": model,
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
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "pk": asset_id,
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
