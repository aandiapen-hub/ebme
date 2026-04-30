from django.http import FileResponse
from reportlab.pdfgen import canvas

from reportlab.pdfbase.pdfmetrics import stringWidth

from PIL import Image

from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from django.contrib.staticfiles import finders

from io import BytesIO

import os

from datetime import datetime
import uuid

# Page size
page_height = 2156
page_width = 3050
margin = 200
space = 10


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


# list lines in PO
def list_jobs(content):
    job_headers = [
        "jobid",
        "customerasset",
        "serialnumber",
        "brandname",
        "model",
        "jobtypename",
        "jobstatus",
        "startdate",
        "enddate",
    ]
    job_lines = []
    for i in range(len(content)):
        job_lines.append(list(map(content[i].get, job_headers)))
    # splitting jobs into chunks for printing on different pages
    job_lines_per_page = 25
    job_lines = [
        job_lines[i : i + job_lines_per_page]
        for i in range(0, len(job_lines), job_lines_per_page)
    ]
    return job_lines


def tableHeaderText():
    headers = [
        "Job ID",
        "Cust Asset",
        "Serial No",
        "Brand",
        "Model",
        "Job Type",
        "Status",
        "Start Date",
        "End Date",
    ]
    styles = getSampleStyleSheet()
    styleH = styles["Normal"]
    styleH.fontSize = 30
    styleH.autoLeading = "max"
    styleH.alignment = 1
    headers = [Paragraph(cell, styleH) for cell in headers]
    return headers


def numberStyle():
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN.fontSize = 30
    styleN.autoLeading = "max"
    styleN.alignment = 2
    return styleN


def textStyle():
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN.fontSize = 30
    styleN.autoLeading = "max"
    styleN.alignment = 0
    return styleN


def gen_job_list(content):
    # list jobs
    job_lines = list_jobs(content)
    no_of_pages = len(job_lines)

    # creating page template
    buff = BytesIO()
    c = canvas.Canvas(buff)
    c.setPageSize((page_width, page_height))

    # draw logo
    logo_file = finders.find("company_info/HD-LOGO.jpeg")
    im = Image.open(logo_file)
    im_width, im_height = im.size
    c.drawImage(
        logo_file,
        100,
        page_height - im_height,
    )

    # set table headers
    headers = tableHeaderText()

    for page in range(no_of_pages):
        # draw logo
        logo_file = finders.find("company_info/HD-LOGO.jpeg")
        im = Image.open(logo_file)
        im_width, im_height = im.size
        c.drawImage(
            logo_file,
            100,
            page_height - im_height,
        )

        job_lines_chunk = job_lines[page]
        x = margin
        y = page_height - margin - 150

        # page title
        c.setFont("Helvetica", 60)
        text = "Job List"
        text_width = stringWidth(text, "Helvetica", 60)
        c.drawString(page_width - text_width - margin, y, text)

        c.setFont("Helvetica", 45)

        space = 50
        y -= space

        style = [("GRID", (0, 0), (-1, -1), 1, colors.black)]

        # format text values in table
        data = [
            [Paragraph(str(cell), textStyle()) for cell in row]
            for row in job_lines_chunk
        ]

        # combine data with headers.
        data = [headers] + data

        table = Table(
            data, style=style, colWidths=[200, 256, 350, 350, 350, 300, 200, 200, 200]
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ]
            )
        )

        w, h = table.wrapOn(c, 0, 0)
        table.drawOn(c, margin, y - h)

        # page count
        page = "Page %s of %s" % (page + 1, no_of_pages)
        print_page(c, page)

        # footer
        footer(c, os.getenv('COMPANY_ADDRESS'))

        c.showPage()
    c.save()
    buff.seek(0)
    return buff


def generate_n_char_id(n: int):
    unique_id = uuid.uuid4()
    short_id = str(unique_id)[:n]
    return short_id


def generate_jobs_list(data):
    pdf = gen_job_list(data)

    dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    uuid = generate_n_char_id(8)
    filename = f"{dt}-{uuid}-joblist.pdf"

    return FileResponse(pdf, as_attachment=True, filename=filename)
