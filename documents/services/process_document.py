from .ocr import extract_text_from_file
from .read_barcode import extract_barcode_from_file, merge_barcode_parsed
from django.db.models import Q


from documents.models import TempUploadGroup
from documents.services.document_parser import temp_group_resolver
from documents.services.ai_processor import extract_group_info_with_ai

def extract_data(group):
    qs = group.temp_uploads.all()

    # check and extract ocr data
    null_ocr_qs = qs.filter(
        Q(ocr_text={}) | Q(ocr_text__isnull=True) | Q(ocr_text='')
    )
    [extract_text_from_file(obj) for obj in null_ocr_qs]
    combined_ocr_text = list(qs.values_list("ocr_text", flat=True))
    group.combined_ocr_text = combined_ocr_text

    # check and extract barcode data
    null_barcode_qs = qs.filter(
        Q(barcode_data={}) | Q(barcode_data__isnull=True)
    )

    [extract_barcode_from_file(obj) for obj in null_barcode_qs]
    barcode_lists = list(qs.values_list("barcode_data", flat=True))
    flattened_barcode_list = [
        barcode for barcode_list in barcode_lists for barcode in barcode_list
    ]
    keys = ("text", "parsed")
    barcode_list = [
        {key: barcode.get(key, None) for key in keys}
        for barcode in flattened_barcode_list
    ]
    group.extracted_json["barcode"] = barcode_list
    group.extracted_json['merged_parsed_barcode'] = merge_barcode_parsed(barcode_list)

    # delete extracted ai data if additional documents has
    # has been added to the temp group for processing.
    if null_ocr_qs.exists() or null_barcode_qs.exists():
        group.extracted_json['ai'] = None

    group.save()


def merge_gs1_ai_data(group, ai_data):
    merged_parsed_barcode = group.extracted_json['merged_parsed_barcode']
    for k, v in merged_parsed_barcode.get('values', {}).items():
        ai_data[k] = v
    return ai_data


def extract_information_from_temp_group(group_id):
    group = TempUploadGroup.objects.get(pk=group_id)

    # extract text and barcode data from images
    extract_data(group)

    # process group documents with ai
    ai_data = group.extracted_json.get('ai', None)
    if ai_data is None:
        ai_data = extract_group_info_with_ai(group)
        group.extracted_json.update(
            {"ai": ai_data, }
        )
    merged_gs1_ai_data = merge_gs1_ai_data(group, ai_data)

    # merge ai and barcode data
    group.extracted_json.update(
        {"merged_gs1_ai": merged_gs1_ai_data}
    )
    group.save(update_fields=["extracted_json"])
    temp_group_resolver(group_id)
