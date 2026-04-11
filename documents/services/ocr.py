from PIL import Image, ImageFilter, ImageOps
import pytesseract
from pytesseract import Output

import math
from statistics import median
from PIL import Image
import pytesseract
from pytesseract import Output


def extract_text(file, min_conf=50):
    with file.file.open('rb') as f:
        img = Image.open(f).convert('L').copy()


    config = (
        "--psm 11 "
    )

    data = pytesseract.image_to_data(
        img,
        config=config,
        output_type=Output.DICT)


    width, height = img.size

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

    file.ocr_text = " ".join(full_text)

    file.ocr_boxes = {
            'ocr_boxes': words,
            'image_size': {
                'width': width,
                'height': height,
            }
    }

    print('ocr text for file', full_text)
    file.save(update_fields=['ocr_text', 'ocr_boxes'])
