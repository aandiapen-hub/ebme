import biip
from PIL import Image
import zxingcpp
from django.core.exceptions import ValidationError
from django.db.models import Q

from assets.models import AssetView, Tblmodel, JobView
from parts.models import Tblpartslist


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
    else:
        gs1_codes = [scanned_code]

    output = {}
    
    for code in gs1_codes:
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
            if es.ai.data_title == "PROD DATE":
                output["PROD_DATE"] = es.date.strftime("%Y-%m-%d")

            if es.ai.data_title == "GIAI":
                output["ASSET_NO"] = es.value[-7:]

    return output


def gs1_resolver(gs1_data):
    output = {}
    known_model = None
    known_part = None
    asset_no = gs1_data.get("ASSET_NO", None)
    gtin = gs1_data.get("GTIN", None)
    serialnumber = gs1_data.get("SERIAL", None)

    output["gtin"] = gtin
    output["gs1"] = gs1_data


    # check for assets
    if asset_no:
        assets = AssetView.objects.filter(assetid=asset_no).first()

    # check for gtin
    if gtin:
        known_model = Tblmodel.objects.filter(gtin=gtin).first()
        output["model"] = known_model
        known_part = Tblpartslist.objects.filter(gtin=gtin).first()
        output["part"] = known_part
        # create model or spare part from gs1_data
        output["create_gtin"] = not known_model and not known_part

    # check for full gs1 match otherwise create asset
    if serialnumber and known_model:

        assets = AssetView.objects.filter(serialnumber=serialnumber, modelid=known_model)
        if assets.exists():
            output["assets"] = assets
            output["jobs"] = assets.first().jobs.all
        else:
            output['create_asset_from_gs1'] = True

    # check for partial gs1 match by serial number
    # return new model creation options from assets with models with gtins
    # exisiting models with gtin should be replicated with new gtin
    if serialnumber and not known_model:
        assets = AssetView.objects.filter(serialnumber__icontains=serialnumber)
        if assets.exists():
            output["partial_asset_match"] = True
            output["assets"] = assets
            #update or create models based on exisiting assets
            models = assets.values_list("modelid", flat=True)
            output["models_with_gtin"] = Tblmodel.objects.filter(
                modelid__in=models, gtin__isnull=False
            )
            print(output["models_with_gtin"])
            output["models_without_gtin"] = Tblmodel.objects.filter(
                modelid__in=models, gtin__isnull=True
            )

    return output


def non_gs1_result(data):
    output = {}
    output["search_term"] = data
    asset_filter = Q(serialnumber__icontains=data) | Q(assetid__icontains=data)
    assets = AssetView.objects.filter(asset_filter).order_by(
        "brandid", "modelid", "serialnumber"
    )
    if assets.count() <= 25:
        output["assets"] = assets
    if assets.count() > 25:
        output["too_many_assets"] = True

    job_filter = Q(jobid__icontains=data)
    jobs = JobView.objects.filter(job_filter).order_by("enddate")

    if assets.count() == 1:
        jobs = assets.first().jobs.all()
    if jobs.count() <= 25:
        output["jobs"] = jobs
    if jobs.count() > 25:
        output["too_many_jobs"] = True

    return output
