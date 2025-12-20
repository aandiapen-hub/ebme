from django.core.cache import cache
from PIL import Image
import zxingcpp
from biip.gs1_messages import GS1Message
from biip.gs1_element_strings import GS1ElementString
from biip import ParseError

def extraction_cache_key(user_id, group):
    return f"extraction:{user_id}:{group}"


def save_extraction_results(user_id, group, results, hours=1):
    if group is None:
        raise ValueError("Group must be provided to save extraction results.")
    key = extraction_cache_key(user_id, group)
    cache.set(key, results, timeout=hours * 60 * 60)

def get_extraction_results(user_id, group):
    key = extraction_cache_key(user_id, group)
    return cache.get(key)

def clear_extraction_results(user_id, group):
    key = extraction_cache_key(user_id, group)
    cache.delete(key)


def quick_scan_barcode(image):
    output = {}
    img = Image.open(image)
    try:
        decoded_data = zxingcpp.read_barcodes(img, text_mode=zxingcpp.Plain)
    except:
        return None
    if len(decoded_data) == 0:
        return('no_barcode_found')
    else:
        code_list = []
        for i, code in enumerate(decoded_data):
            # code_list.append(code.text)
            if code.content_type == zxingcpp.GS1:
                output.update(parse_gs1code(code.text))
            else:
                output[f'{image.name}_value{i}'] = code.text
    output['raw_code'] = code_list
    return output


def parse_gs1code(data):
    output = {}
    try:
        x = GS1Message.parse(data)
        for es in x.element_strings:
            if es.ai.data_title == 'PROD DATE':
                output['PROD_DATE'] = es.date.strftime('%Y-%m-%d')
            else:
                output[es.ai.data_title] = es.value
                if es.ai.data_title == 'GIAI':
                    output['ASSET_NO'] = es.value[-7:]

    except ParseError as e:
        print(f'error passing data as GS1 message ({e})')

    # read individual gs1 element
    try:
        data = data.translate(str.maketrans('', '', "_:,()"))
        data = GS1ElementString.extract(data)
        output[data.ai.data_title] = data.value

    except ParseError as e:
        print(str(e))
    return output

