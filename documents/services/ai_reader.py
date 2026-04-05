from openai import OpenAI

import base64
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
import zxingcpp
from biip.gs1_messages import GS1Message
from biip.gs1_element_strings import GS1ElementString
import json
import os


def openaiImageProcessing(files):
    client = OpenAI(
        api_key=os.getenv("OPENAI_KEY"), organization="org-gRDyA6SKcK90YA5ar9lTpdQ6"
    )

    encoded_images = process_images(files)
    barcode_prompt = scan_barcode(files)

    # gpt promt
    prompt = f"Based on the information in the photo I provided and from online sources,\
    give me the brand, model name, model reference number and model description\
    of the medical device. If the brand and trade name are ambiguous, provide me with the top 3 possible equipment brands.\
    Provide me with 3 possible categories using medical device nomenclature.\
    OCR software was used to recognise text in this picture.\
    {barcode_prompt}\
    Provide the results in a valid json format with the\
    following keys:GTIN, SERIAL, ASSET_NO, brands, model_name, model_description,\
    ,PROD_DATE,categories.\
    If document is not eqiupment labels or IDs, return a json with key document_type and value unknown."

    content = [{"type": "text", "text": prompt}] + encoded_images

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    ai_response = response.choices[0].message.content

    return json.loads(ai_response)


def process_images(files):
    encoded_images = []
    for file in files:
        if file.mime_type == "image/jpeg":
            with open(file.file.path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            encoded_images.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}",
                    },
                }
            )

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
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}",
                        },
                    }
                )

    return encoded_images


def encode_image(image):
    return base64.b64encode(image.read()).decode("utf-8")


def scan_barcode(files):
    output = {}
    for file in files:
        img = Image.open(file.file.path)
        try:
            decoded_data = zxingcpp.read_barcodes(img, text_mode=zxingcpp.Plain)
        except:
            pass

        if len(decoded_data) == 0:
            continue

        else:
            # code_list = []
            for i, code in enumerate(decoded_data):
                # code_list.append(code.text)
                if code.content_type == zxingcpp.GS1:
                    output.update(parse_gs1code(code.text))
                else:
                    output[f"{file.file.name}_value{i}"] = code.text
        # output['code'] = code_list
    return output


def parse_gs1code(data):
    output1 = {}
    try:
        x = GS1Message.parse(data)
        for es in x.element_strings:
            if es.ai.data_title == "PROD DATE":
                output1["PROD_DATE"] = es.date.strftime("%Y-%m-%d")

            else:
                output1[es.ai.data_title] = es.value
                if es.ai.data_title == "GIAI":
                    output1["ASSET_NO"] = es.value[-7:]

    except:
        data = data.translate(str.maketrans("", "", "_:,()"))
        data = GS1ElementString.extract(data)
        output1[data.ai.data_title] = data.value
    return output1


def barcode_reader_ai(files):
    return openaiImageProcessing(files)

