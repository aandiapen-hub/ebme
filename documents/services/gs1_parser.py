import biip
from PIL import Image
import zxingcpp
from django.core.exceptions import ValidationError
from django.db.models import Q

from assets.models import AssetView, Tblmodel, JobView
from parts.models import Tblpartslist


def data_builder(
    # barcode and gtin
    parsed_gs1=None,  # raw gs1 data
    gtin=None,
    add_gtin=False,

    # asset information
    asset_id=None,  # confirmed asset
    assets=None,
    too_many_assets=False,

    create_asset=None,  # true or false

    # job information
    jobs=None,
    too_many_jobs=False,

    # model information
    model_id=None,  # model matching gtin
    models_with_gtin=None,  # models without gtin from assets with serial number
    models_without_gtin=None,  # models with gtin from assets with serial number
    suggested_new_model_names=None,
    suggested_model_brands=None,
    suggested_model_categories=None,

    # spare part information
    part_id=None,  # part matching gtin
    suggested_new_part_names=None,
    suggested_part_brands=None,
    suggested_part_categories=None,
):

    return {
        'gs1': {
            'parsed_gs1': parsed_gs1,
            'gtin': gtin,
            'add_gtin': add_gtin,
        },
        'asset': {
            'asset_id': asset_id,
            'assets': assets or [],
            'create_asset': create_asset,
            'too_many_assets': too_many_assets,
        },
        'job': {
            'jobs': jobs,
            'too_many_jobs': too_many_jobs,
        },
        'model': {
            'model_id': model_id,
            'models_with_gtin': models_with_gtin,
            'models_without_gtin': models_without_gtin or [],
            'suggested_new_name': suggested_new_model_names or [],
            'suggested_brands': suggested_model_brands or [],
            'suggested_categories': suggested_model_categories or [],
        },
        'part': {
            'part_id': part_id,
            'suggested_new_name': suggested_new_part_names or [],
            'suggested_brands': suggested_part_brands or [],
            'suggested_categories': suggested_part_categories or [],

        }
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
        print('code to be parsed from file', gs1_codes)
    else:
        gs1_codes = [scanned_code]
        print('code to be parsed from text given', gs1_codes)

    output = {}

    for code in gs1_codes:
        # ignore internal codes
        if code.startswith('9'):
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


def gs1_resolver(parsed_gs1):
    output = data_builder()

    asset_no = parsed_gs1.get("ASSET_NO", None)
    gtin = parsed_gs1.get("GTIN", None)
    serialnumber = parsed_gs1.get("SERIAL", None)

    output["gtin"] = gtin
    output["gs1"] = parsed_gs1

    # check for asset number on database
    if asset_no:
        assets = AssetView.objects.filter(assetid=asset_no)
        if assets.exists():
            output['asset'] = assets.first()
            output["jobs"] = assets.first().jobs.all
            return output
        else:
            output['create_asset_from_gs1'] = True

    # check for gtin
    if gtin:
        known_model = Tblmodel.objects.filter(gtin=gtin).first()
        output["model"] = known_model
        known_part = Tblpartslist.objects.filter(gtin=gtin).first()
        output["part"] = known_part
        if known_part:
            return output
        # create model or spare part from gs1_data
        output["add_gtin"] = not known_model and not known_part

    # check for full gs1 match otherwise create asset
    if serialnumber and known_model:
        assets = AssetView.objects.filter(serialnumber=serialnumber, modelid=known_model)
        if assets.exists():
            output["asset"] = assets.first()
            output["jobs"] = assets.first().jobs.all
            return output
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
            # update or create models based on exisiting assets
            models = assets.values_list("modelid", flat=True)
            output["models_with_gtin"] = Tblmodel.objects.filter(
                modelid__in=models, gtin__isnull=False
            )
            output["models_without_gtin"] = Tblmodel.objects.filter(
                modelid__in=models, gtin__isnull=True
            )
        output['create_asset_from_gs1'] = True

    return output


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
        output['search_term'] = scanned_code
        return output
    else:
        output = gs1_resolver(decoded_info)
        output['search_term'] = f"{output.get('gs1').get('SERIAL', '')} {output.get('gs1').get('ASSET_NO', '')}"
        return output
