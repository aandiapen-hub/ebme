import ast
import json
from openai import OpenAI
import base64
from pdf2image import convert_from_bytes
from io import BytesIO

import os


def openaiImageProcessing(files):

    client = OpenAI(
        api_key = os.getenv('OPENAI_KEY'),
        organization = 'org-gRDyA6SKcK90YA5ar9lTpdQ6')
    

    encoded_images = process_images(files)
    
    #chat gpt prompting based of category of document being fed.
    prompt = f"We need to get the information from a service report from a service of a medical device.\
        Based on the information in the photo and text information I provided,\
        give me the Serial Number, Job Type, Job Status, Job report Number, Reported Fault ,Work call date, work start date, work end date, summary of work done and\
        any further repair work required.\
        Highlight any software update, faults and non-compliant measurements in the work done.\
        Give the dates in ISO format. The job type must be either PPM, Repair or Decommissioning.\
        The Job status should be either In Progress or Completed.\
        Return the result in a valid JSON format with keys serialnumber,\
        jobtypename, jobstatus, job_no, reported_fault, call_date, jobstartdate, jobenddate, workdone, further_work."
                         
    
    content = [{"type": "text", "text": prompt}] + encoded_images
    
    
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature = 1,
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    ai_response = response.choices[0].message.content
    print(ai_response)
    if ai_response:  
        return json.loads(ai_response)
    else:
        return []
    

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
        
def encode_image(image):
       with open(image,'rb') as file: 
        return base64.b64encode(file.read()).decode('utf-8')






def report_reader(files):
    return openaiImageProcessing(files)
    