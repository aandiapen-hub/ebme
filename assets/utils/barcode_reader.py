from biip.gs1_messages import GS1Message
from biip.gs1_element_strings import GS1ElementString

import zxingcpp
from PIL import Image


   
def scan_barcode(files):
    images = [file.file.path for file in files]

    output = {}
    for image in images:
        img = Image.open(image)
        try:
            decoded_data = zxingcpp.read_barcodes(img,text_mode=zxingcpp.Plain)
        except:
            pass
            
        if len(decoded_data) == 0:
            continue
            
        else:
            #code_list = []
            for i, code in enumerate(decoded_data):
                #code_list.append(code.text)
                if code.content_type == zxingcpp.GS1:
                    output.update(parse_gs1code(code.text))
                """else:
                    output[f'{image.name}_value{i}'] = code.text"""
        #output['code'] = code_list
    return output


def parse_gs1code(data):
    output1={}
    try:
        x = GS1Message.parse(data)
        for es in x.element_strings:
            if es.ai.data_title == 'PROD DATE':
                   output1['PROD_DATE'] = es.date.strftime('%Y-%m-%d')
                   
            else:
                output1[es.ai.data_title] = es.value
                if es.ai.data_title == 'GIAI':
                    output1['ASSET_NO'] = es.value[-7:]

           
    except:
        data = data.translate(str.maketrans('', '', "_:,()"))
        data = GS1ElementString.extract(data)
        output1[data.ai.data_title] = data.value
    return output1



