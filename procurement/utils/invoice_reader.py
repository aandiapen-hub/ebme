import ast
from openai import OpenAI
from datetime import datetime
import base64
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO

import os


def openaiImageProcessing(files):

    client = OpenAI(
        api_key = os.getenv('OPENAI_KEY'),
        organization = 'org-gRDyA6SKcK90YA5ar9lTpdQ6')
    

    encoded_images = process_images(files)
    
    #chat gpt prompting based of category of document being fed.
    prompt = f"This is an invoice. It contains information about the PO number, Invoice date, Invoice Due date, amount due without VAT and\
    amount due with VAT. The PO number should start with '51'.\
    Return the result in a valid JSON format with keys po, invoice_no, invoice_date, invoice_due_date, invoice_amount, amount_incl_vat.\
    Give the dates in iso format\
    If document is not an invoice, return a json with key document_type and value unknown."
                         
    
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
    try:
        output = ast.literal_eval(ai_response)
    except:
        output = {"error":"Could not parse the response. Please try again."}
    return output
    

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
                pdf_bytes = pdf_file.read()  
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







def invoice_reader(files):
    return openaiImageProcessing(files)
    