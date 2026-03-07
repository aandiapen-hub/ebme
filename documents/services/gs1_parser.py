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

    for code in gs1_codes:
        output = {}
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
            else:
                if es.ai.data_title == "GIAI":
                    output["ASSET_NO"] = es.value[-7:]


def gs1_resolver(gs1_data):
    output = {}
    model = None
    part = None

    asset_no = gs1_data.get("ASSET_NO", None)
    gtin = gs1_data.get("GTIN", None)
    serialnumber = output.get("SERIAL", None)

    # check for gtin
    if gtin:
        model = Tblmodel.objects.filter(gtin=gtin).first()
        output["model"] = model
        part = Tblpartslist.objects.filter(gtin=gtin).first()
        output["part"] = part

    output["create_gtin"] = not model and not part

    # check for assets
    if asset_no:
        assets = AssetView.objects.filter(assetid=asset_no).first()

    if serialnumber and model:
        assets = AssetView.objects.filter(serialnumber=serialnumber, modelid=model)
        # if asset exists then go to asset
    elif serialnumber:
        assets = AssetView.objects.filter(serialnumber=serialnumber)
    else:
        assets = None

    output["assets"] = assets
    output["create_asset"] = not assets.exists()


def non_gs1_resolver(data):
    output = {}

    asset_filter = Q(serialnumber=data) | Q(assetid=data)
    output["assets"] = AssetView.objects.filter(asset_filter)

    job_filter = Q(serialnumber=data) | Q(jobid=data) | Q(assetid=data)
    output["jobs"] = JobView.objects.filter(job_filter)
