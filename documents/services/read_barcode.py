from PIL import Image
import zxingcpp
from documents.services.gs1_parser import parse_gs1code


def extract_barcode(file):
    with file.file.open('rb') as f:
        image = Image.open(f).convert('L').copy()
    barcodes = zxingcpp.read_barcodes(image, text_mode=zxingcpp.Plain)

    if len(barcodes) == 0:
        return None

    decoded_barcodes = []

    width, height = image.size

    for barcode in barcodes:
        print('barcode', barcode.text.replace('(', '').replace(')', ''), barcode.format)
        pos = barcode.position
        points = [
            {"x": pos.top_left.x, "y": pos.top_left.y},
            {"x": pos.top_right.x, "y": pos.top_right.y},
            {"x": pos.bottom_right.x, "y": pos.bottom_right.y},
            {"x": pos.bottom_left.x, "y": pos.bottom_left.y},
        ]

        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]

        x = min(xs)
        y = min(ys)
        w = max(xs) - x
        h = max(ys) - y

        result = {
            "text": barcode.text.replace('(', '').replace(')', ''),
            "format": str(barcode.format),
            "parsed": parse_gs1code(scanned_code=barcode.text.replace('(', '').replace(')', '')),
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "x_pct": round((x / width) * 100, 4),
            "y_pct": round((y / height) * 100, 4),
            "w_pct": round((w / width) * 100, 4),
            "h_pct": round((h / height) * 100, 4),
        }
        decoded_barcodes.append(result)

    file.barcode_data = decoded_barcodes
    file.save(update_fields=['barcode_data'])





