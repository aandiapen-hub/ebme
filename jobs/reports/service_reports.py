from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from PIL import Image
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

from io import BytesIO

from datetime import datetime
import uuid
import os
from django.contrib.staticfiles import finders

# Page size
page_width = 2156
page_height = 3050
margin = 200


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 30)
    canvas.drawString(margin, 50, doc)
    canvas.restoreState()


def print_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 30)
    canvas.drawString(page_width - 300, 50, doc)
    canvas.restoreState()


short_keys = {
    "customer": "Customer",
    "jobid": "Job ID",
    "customerasset": "Cust Asset",
    "serialnumber": "Serial No",
    "brandnamd": "Brand",
    "model": "Model",
    "jobtypename": "Job Type",
    "jobstatus": "Status",
    "startdate": "Start Date",
    "enddate": "End Date",
    "technician_name": "Technician",
}

long_keys = {
    "workdone": "Work Done",
    "testsperjob": "Checklist",
    "partsperjob": "Spare Parts",
}


# paragraph style
def draw_paragraph(canvas, msg, x, y, max_width, max_height):
    style = ParagraphStyle(name="Normal", fontName="Helvetica", fontSize=45, leading=50)
    style.wordWrap = "CJK"
    message = Paragraph(msg, style=style)
    draw_paragraph.w, draw_paragraph.h = message.wrap(max_width, max_height)
    message.drawOn(canvas, x, y - draw_paragraph.h)


def create_service_report(content):
    no_of_jobs = len(content)

    buff = BytesIO()
    c = canvas.Canvas(buff)
    c.setPageSize((page_width, page_height))
    no_of_jobs = len(content)

    for i in range(no_of_jobs):
        # draw logo
        logo_file = finders.find("company_info/HD-LOGO.jpeg")
        im = Image.open(logo_file)
        im_width, im_height = im.size
        c.drawImage(
            logo_file,
            100,
            page_height - im_height,
        )
        x = margin
        y = page_height - 1.5 * margin

        # document title
        c.setFont("Helvetica", 60)
        text = "Service report"
        text_width = stringWidth(text, "Helvetica", 60)
        c.drawString(page_width - text_width - margin, y, text)

        c.setFont("Helvetica", 45)

        space = 50
        y -= 5 * space

        # draw keys with short fields
        x = margin
        y1 = y

        for key, value in short_keys.items():
            text = content[i].get(key)

            # format date to preferred display format. Also, if date if not valid, then return a blank string
            if "date" in key:
                try:
                    text = text.strftime("%d-%b-%Y")
                except:
                    text = ""

            c.setFont("Helvetica-Bold", 45)
            c.drawString(x, y1, f"{value}:")
            c.setFont("Helvetica", 45)
            c.drawString(x + 275, y1, str(text))

            # space below customer
            if key == "customer":
                y1 -= 2 * space
            else:
                y1 -= space

            # split column
            if key == "model":
                x = page_width / 2
                y1 = y - 2 * space

        y = y1 - space
        # drawline
        c.line(margin, y, page_width - margin, y - 2)
        y -= 1.5 * space

        # draw keys with long fields
        for key, value in long_keys.items():
            text = content[i].get(key, "None")

            c.setFont("Helvetica-Bold", 45)
            c.drawString(margin, y, f"{value}:")

            text = text.replace("\n", "<br/>")
            text = "" if text is None else text

            draw_paragraph(c, text, margin, y, page_width - 2 * margin, 500)

            y -= draw_paragraph.h + space
            # drawline
            c.line(margin, y, page_width - margin, y - 2)
            y -= 1.5 * space

        # Total Cost
        key = "total_cost"
        text = content[i].get(key, "0.00")
        c.drawString(margin, y, f"Total Cost of Parts: £{text}")
        y -= space

        # footer
        footer(c, os.getenv('COMPANY_ADDRESS'))

        # page count
        page = "Page %s of %s" % (i + 1, no_of_jobs)
        print_page(c, page)

        # next page
        i += 1
        c.showPage()
    c.save()
    buff.seek(0)
    return buff


def generate_n_char_id(n: int):
    unique_id = uuid.uuid4()
    short_id = str(unique_id)[:n]
    return short_id


def generate_service_report(data):
    pdf = create_service_report(data)
    dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    uuid = generate_n_char_id(8)
    filename = f"{dt}-{uuid}-servicereports.pdf"

    return FileResponse(pdf, as_attachment=True, filename=filename)

