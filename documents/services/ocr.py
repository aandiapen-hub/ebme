from PIL import Image
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_bytes


def extract_text_from_image(file, min_conf=50):
    print('extracting ocr for file:', repr(file))
    with file.file.open('rb') as f:
        img = Image.open(f).convert('L').copy()
    return ocr(img)


def ocr(opened_img, min_conf=50, page_num=0):
    config = (
        "--psm 11 "
    )

    data = pytesseract.image_to_data(
        opened_img,
        config=config,
        output_type=Output.DICT)

    width, height = opened_img.size

    words = []
    full_text = []

    for i, text in enumerate(data['text']):
        text = text.strip()
        if not text:
            continue

        conf = float(data["conf"][i])
        if conf < min_conf or len(text)<=3:
            continue
        x = data['left'][i]
        y = data['top'][i]
        w = data['width'][i]
        h = data['height'][i]

        word = {
            'text': text,
            'conf': conf,
            'page': page_num,
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'x_pct': round((x / width) * 100, 4),
            'y_pct': round((y / height) * 100, 4),
            'w_pct': round((w / width) * 100, 4),
            'h_pct': round((h / height) * 100, 4),
        }

        words.append(word)
        full_text.append(text)

    output = {}
    output['ocr_text'] = " ".join(full_text)

    output['ocr_boxes'] = words

    print('ocr text for file', full_text)
    return output


def extract_text_from_pdf(file):
    print("extracting text from pdf", repr(file))

    with file.file.open('rb') as f:
        pdf_bytes = f.read()

    # convert pdf to list of PIL images
    pages = convert_from_bytes(pdf_bytes, dpi=300)

    all_text = ""
    all_words = []

    for page_num, img in enumerate(pages):
        img = img.convert('L')  # grayscale

        data = ocr(img)
        all_words.append(data['ocr_boxes']) 
        all_text += data['ocr_text']

    output = {}
    output['ocr_text'] = all_text
    output['ocr_boxes'] = all_words
    return output

def extract_text_from_file(file):
    if 'image' in file.mime_type:
        extracted_data = extract_text_from_image(file)
    elif 'pdf' in file.mime_type:
        extracted_data = extract_text_from_pdf(file)
    else:
        pass

    file.ocr_text = extracted_data['ocr_text']
    file.ocr_boxes = extracted_data['ocr_boxes']

    file.save(update_fields=['ocr_text', 'ocr_boxes'])
