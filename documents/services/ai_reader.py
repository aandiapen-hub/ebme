from openai import OpenAI

import base64
from pdf2image import convert_from_bytes
from io import BytesIO
import os
from .ocr import extract_text
from .read_barcode import extract_barcode, merge_barcode_parsed
from .gs1_parser import gs1_resolver
from django.db.models import Q


from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from documents.models import TempUploadGroup, TemporaryUpload, DocumentTypes
from documents.services.gs1_parser import temp_group_resolver


class AssetData(BaseModel):
    GTIN: Optional[str] = None
    SERIAL: Optional[str] = None
    ASSET_NO: Optional[str] = None
    PROD_DATE: Optional[date] = None

    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None

    brand_name_options: list[str] = Field(default_factory=list)
    model_name_options: list[str] = Field(default_factory=list)
    category_name_options: list[str] = Field(default_factory=list)

    model_description: Optional[str] = None


PROMPT_CONTENT = {
    DocumentTypes.ASSET_DATA.value: {
        "user_prompt": "Get information about the medical equipment from the images\
                            and decoded text and gs1 decoded informations. gs1 decoded information is always acurate. If the information\
                            is not clear, return none, do not guess. Give name options that can be used for keyword lookup in a database",
        "system_prompt": "You are a biomedical equipment administrator with expertise in cataloging\
                        medical equipment and devices on a database.",
    }
}


def openaiImageProcessing(group):
    client = OpenAI(
        api_key=os.getenv("OPENAI_KEY"), organization="org-gRDyA6SKcK90YA5ar9lTpdQ6"
    )

    qs = TemporaryUpload.objects.filter(group=group)
    document_type = group.document_type_id

    encoded_images = encode_images(qs)

    # compbine extracted data for the group as perparation for LLM prompt
    gs1 = repr(group.extracted_json["barcode"])
    decoded_text = [item for item in qs.values_list("ocr_text", flat=True) if item]

    # start building prompt
    content = [
        {"type": "input_text", "text": PROMPT_CONTENT[document_type]["user_prompt"]}
    ]
    if gs1:
        content.append({"type": "input_text", "text": gs1})
    if decoded_text:
        content.append({"type": "input_text", "text": ",".join(decoded_text)})

    content = content + encoded_images

    response = client.responses.parse(
        model="gpt-4o",
        temperature=0.3,
        input=[
            {
                "role": "system",
                "content": PROMPT_CONTENT[document_type]["system_prompt"],
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        text_format=AssetData,
    )
    return response.output_parsed


def encode_images(files):
    encoded_images = []
    for file in files:
        if file.mime_type == "image/jpeg":
            with open(file.file.path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")

        elif file.mime_type == "application/pdf":
            pdf_bytes = file.file.path.read()
            pages = convert_from_bytes(pdf_bytes)
            for page in pages:
                im_file = BytesIO()
                page.save(im_file, "JPEG")
                im_bytes = im_file.getvalue()
                img_b64 = base64.b64encode(im_bytes).decode("utf-8")

        encoded_images.append(
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{img_b64}",
            }
        )
    return encoded_images


def extract_data(group):
    qs = group.temp_uploads.all()

    # check and extract ocr data
    null_ocr_qs = qs.filter(
        Q(ocr_text={}) | Q(ocr_text__isnull=True) | Q(ocr_text='')
    )
    print('count of images missing ocr:', null_ocr_qs.count())
    [extract_text(obj) for obj in null_ocr_qs]
    combined_ocr_text = list(qs.values_list("ocr_text", flat=True))
    group.combined_ocr_text = combined_ocr_text

    # check and extract barcode data
    null_barcode_qs = qs.filter(
        Q(barcode_data={}) | Q(barcode_data__isnull=True)
    )
    print('count of images missing barcode:', null_barcode_qs.count())
    [extract_barcode(obj) for obj in null_barcode_qs]
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
    group.save()


def merge_gs1_ai_data(group, ai_data):
    merged_parsed_barcode = group.extracted_json['merged_parsed_barcode']
    for k, v in merged_parsed_barcode.get('values', {}).items():
        ai_data[k] = v
    return ai_data


def extract_information_with_ai(group_id):
    group = TempUploadGroup.objects.get(pk=group_id)

    # extract text and barcode data from images
    extract_data(group)

    # process group documents with ai
    ai_data = group.extracted_json.get('ai', None)
    if ai_data is None:
        ai_data = openaiImageProcessing(group).model_dump(mode="json")
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
