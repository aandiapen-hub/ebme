from openai import OpenAI

import base64
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
import ast
import os


def openaiImageProcessing(files):

    client = OpenAI(
        api_key = os.getenv('OPENAI_KEY'),
        organization = 'org-gRDyA6SKcK90YA5ar9lTpdQ6')
    

    encoded_images = process_images(files)
    
    #chat gpt prompting based of category of document being fed.
    prompt = f"We need to get the information from a delivery note that includes delivered and outstanding items.\
    Based on the information in the photo and text information I provided,\
    give me the Purchase Order Number, Delivery Note number, despatch date, items delivered. The items should\
    have their Part Number, Description and Quantity delivered and quantity outstanding/to follow if avaiable.\
    The PO number should start with '51'.\
    Return the result in a valid JSON format with keys PO, DelNote, Date, Items. The keys in items\
    should be item, Description, qty, QtyOutstanding.\
    If document is not a delivery note , return a json with key document_type and value unknown."

    
    content = [{"type": "text", "text": prompt}] + encoded_images
    
    
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature = 0.3,
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    
    ai_response = response.choices[0].message.content
    return ast.literal_eval(ai_response)
    

def process_images(files): 
    encoded_images = []
    for file in files:
        mime_type = file.mime_type
        file_path = file.file.path
        if mime_type == 'image/jpeg':
            img_bytes = encode_image(file_path)
            encoded_images.append({ 
                                    "type": "image_url",
                                    "image_url": {
                                        'url':f"data:image/jpeg;base64,{img_bytes}",}
                                    })

        elif mime_type == 'application/pdf':
            with open(file_path,'rb') as pdf_file:
                pdf_bytes = pdf_file.read()  # <-- this is the fix
            pages = convert_from_bytes(pdf_bytes)
            for page in pages:
                im_file = BytesIO()
                page.save(im_file, 'JPEG')
                im_bytes = im_file.getvalue()
                img_b64 = base64.b64encode(im_bytes).decode('utf-8')

                encoded_images.append({ 
                                            "type": "image_url",
                                            "image_url": {
                                                'url':f"data:image/jpeg;base64,{img_b64}",}
                                            })

    return encoded_images
        
def encode_image(file_path):
    with open(file_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def delivery_note_reader(files):
    return openaiImageProcessing(files)
    