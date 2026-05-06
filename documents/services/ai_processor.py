from openai import OpenAI

import base64
from pdf2image import convert_from_bytes
from io import BytesIO
import os


from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from documents.models import TemporaryUpload, DocumentTypes
from assets.models import Tbljobstatus, Tbljobtypes


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


class JobData(BaseModel):
    job_ref: Optional[str] = None
    SERIAL: Optional[str] = None
    ASSET_NO: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cal_date: Optional[date] = None

    workdone: Optional[str] = None
    jobtypeid: Optional[int] = None
    jobstatusid: Optional[int] = None


def jobtypeid_options():
    return list(Tbljobtypes.objects.all().values('pk', 'jobtypename'))


def jobstatusid_options():
    return list(Tbljobstatus.objects.all().values('pk', 'jobstatusname'))


def format_options(title, options, id_field, name_field):
    options_string = [f"{o[id_field]}:{o[name_field]}" for o in options]
    output = f"{title}: {chr(10).join(options_string)})"
    return output


def service_report_system_prompt():
    return f"""You are a specialist admin transfering medical equipment service records
            into a medical equipment database.
            You must choose appropriate job type and job status from the lists below.
            - jobtype from {format_options('jobtype', jobtypeid_options(), 'pk', 'jobtypename')}
            - jobstatus from {format_options('jobstatus', jobstatusid_options(), 'pk', 'jobstatusname')}"""


PROMPT_CONTENT = {
    DocumentTypes.ASSET_DATA.value: {
        "user_prompt": """Get information about the medical equipment from the images
                            and decoded text and gs1 decoded informations. gs1 decoded information is always acurate. If the information
                            is not clear, return none, do not guess. Give name options that can be used for keyword lookup in a database""",
        "system_prompt": """You are a biomedical equipment administrator with expertise in cataloging
                        medical equipment and devices on a database.""",
        "response_format": AssetData,
    },
    DocumentTypes.SERVICE_REPORT.value: {
        "user_prompt": "Get information about the work carried out on a medical equipment from the service report.",
        "system_prompt": service_report_system_prompt,
        "response_format": JobData,
    },
}


def get_system_prompt(system_prompt):
    return system_prompt() if callable(system_prompt) else system_prompt


def extract_group_info_with_ai(group):
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
                "content": get_system_prompt(PROMPT_CONTENT[document_type]["system_prompt"]),
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        text_format=JobData,
    )
    return response.output_parsed.model_dump(mode="json")


def encode_images(files):
    encoded_images = []
    for file in files:
        if file.mime_type == "image/jpeg":
            with open(file.file.path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            encoded_images.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{img_b64}",
                }
            )

        elif file.mime_type == "application/pdf":
            with open(file.file.path, 'rb') as f:
                pdf_bytes = f.read()
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


