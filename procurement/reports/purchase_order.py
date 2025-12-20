
from django.http import FileResponse
from reportlab.pdfgen import canvas

from reportlab.pdfbase.pdfmetrics import stringWidth

from PIL import Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.contrib.staticfiles import finders



from io import BytesIO
import base64
import os
from datetime import datetime
import uuid

#Company Name
company_name = os.getenv('COMPANY_NAME')
#Page size
page_width = 2156
page_height = 3050
margin =200
space = 30

#paragraph style
def draw_paragraph(canvas, msg, x, y, max_width, max_height):
    style = ParagraphStyle(
            name='Normal',
            fontName='Helvetica',
            fontSize=45, leading=50)
    message = Paragraph(msg, style=style)
    w, h = message.wrap(max_width, max_height)
    message.drawOn(canvas, x, y - h)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 30)
    text_width = stringWidth(doc,'Helvetica',30)
    xstart = page_width/2-text_width/2
    canvas.drawString(xstart, margin, doc)
    canvas.restoreState()
    

#list lines in PO
def listPolines(data):
    po_lines_headers = ['qty_ordered',  'partnumber',
                'line_description','unit_price', 'line_price']
    po_lines = []
    for i in range(len(data)):    
        po_lines.append(list(map(lambda attr: str(getattr(data[i], attr)), po_lines_headers)))
    return po_lines

def tableHeaderText():
    po_lines = ['Qty','Item ref','Item Description', 
             'Unit Price', 'Line Price']
    styles = getSampleStyleSheet()
    styleH = styles['Normal']
    styleH.fontSize = 30
    styleH.autoLeading = 'max'
    styleH.alignment = 1
    headers = [Paragraph(cell, styleH) for cell in po_lines]
    return headers

def numberStyle():
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 30
    styleN.autoLeading = 'max'
    styleN.alignment = 2
    return styleN

def textStyle():
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 30
    styleN.autoLeading = 'max'
    styleN.alignment = 0
    return styleN

conditions = "1. Enter this order in accordance with the prices, terms, delivery method and \
specifications listed above.\n\
2. Please notifiy us immediately if you are unable to ship as specified.\n\
3.Send all correspondence to:\n\
Rica Faltado\n\
Kemp House,\n\
124 City Road,\n\
London, EC1V 2NX\n\
07887 846 597"


def  gen_purchase_order(data):
    header = data[0]


    gen_purchase_order.po_id = data[0].po_id
    
    buff = BytesIO()
    c = canvas.Canvas(buff)
    c.setPageSize((page_width,page_height))

     
    #draw logo
    logo_file = finders.find('HD-LOGO.jpeg')
    im = Image.open(logo_file)
    im_width,im_height = im.size
    c.drawImage(logo_file,100, page_height-im_height, )
    x = margin
    y =  page_height-1.5*margin
    
    x = margin
    y =  page_height-2*margin
    
    #document title
    c.setFont('Helvetica',80)
    text = 'Purchase Order'
    text_width = stringWidth(text,'Helvetica',80)
    c.drawString(page_width-text_width-margin,y,text )
    
    c.setFont('Helvetica',45)
    x = page_width-margin
    y= y-space-100
    
    #right header
    right_headers = {"Purchase order": "po_id",
                     "Date Raised":"date_raised",
                     "Supplier ID": "supplier_id_id",}
    
    #print purchase order
    centerx = 250
    for key,value in right_headers.items():
        
        text = key + ": "
        text_width = stringWidth(text,'Helvetica-Bold',45)
        c.setFont('Helvetica-Bold',45)
        c.drawString(page_width-margin-text_width-centerx,y,text)
        
        key_value = getattr(header,value)
        c.setFont('Helvetica',45)
        c.drawString(page_width-margin-centerx,y, str(key_value) )
        y-=2*space

    #print supplier
    ysupplier = y
    
    text = "Supplier"
    c.setFont('Helvetica-Bold',45)
    c.drawString(margin,ysupplier,text)
    ysupplier-= space

    supplier_name = getattr(header,'supplier_name')
    first_line = getattr(header,'addr_first_line')
    postcode = getattr(header,'addr_postcode')
    
    text = '<br />'.join([supplier_name,first_line,postcode])
    draw_paragraph(c, text, margin, ysupplier, 500, 500)

    ysupplier-=space
       
    #print delivery info
    ydelivery = y
    xsupplier = page_width//2
    
    text = "Ship To"
    c.setFont('Helvetica-Bold',45)
    c.drawString(xsupplier,ydelivery,text)
    ydelivery-= space

    del_name = getattr(header,'contact','')
    first_line = getattr(header,'first_line','')
    postcode = getattr(header,'postcode','')
    
    text = '<br />'.join([del_name,first_line,postcode])
    draw_paragraph(c, text, xsupplier, ydelivery, 500, 500)

    ydelivery-=space
    
    y =  min(ysupplier,ydelivery)-300
    
    #list po lines
    po_lines = listPolines(data)
    style=[('GRID',(0,0),(-1,-1),1,colors.black)]
    
    headers = tableHeaderText()
    
    #format text values in table
    data = [[Paragraph(cell, textStyle())  if i<3 else f"{float(cell):.2f}" for i,cell in enumerate(row)] for row in po_lines]
    
    #format money values in table
    data = [[Paragraph(cell, numberStyle())  if i>=3 else cell for i,cell in enumerate(row)] for row in data]
    
    #combine data with headers.
    data = [headers] + data
    
    table = Table(data,style=style,colWidths=[100,300,956,200,200] )
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                               ('BOTTOMPADDING',(0,0),(-1,-1),20),
                               ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
                               ]))
    
    w, h = table.wrapOn(c, 0,  0)
    table.drawOn(c, margin, y-h)
    y = y-h-2*space
    
    #write totals
    totals_headers = {"Sub Total":"sub_total",
                      " VAT":"vat_amount" ,
                      "Total":"po_total"}
    for key,value in totals_headers.items():
        
        text = key + ": "
        text_width = stringWidth(text,'Helvetica-Bold',45)
        c.setFont('Helvetica-Bold',45)
        c.drawString(page_width-margin-text_width-centerx,y,text)
        
        key_value = getattr(header,value,'0')
        try:
            key_value = f"£{float(key_value):.2f}"
        except (TypeError, ValueError):
            key_value = "£0.00"
        text_width = stringWidth(key_value,'Helvetica',45)
        c.setFont('Helvetica',45)
        c.drawString(page_width-margin-text_width,y,key_value )
        y-=2*space
    
    
    #terms and conditions
    
    textobject = c.beginText(margin,margin+10*space)
    c.setFont('Helvetica', 30)
    for line in conditions.splitlines(False):
        textobject.textLine(line.rstrip())
    c.drawText(textobject)
    y -= space
       
    #footer
    footer(c, os.getenv('COMPANY_ADDRESS'))
    
    c.showPage()
    c.save()
    buff.seek(0)
    return buff
    
    



def generate_n_char_id(n: int):
    unique_id = uuid.uuid4()
    short_id = str(unique_id)[:n]
    return short_id
    


def print_po(data):
    if data is None or len(data) == 0:
        raise ValueError("No data provided to generate purchase order.")
    pdf=gen_purchase_order(data)
    

    
    dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    uuid = generate_n_char_id(8)
    filename = f"purchase_orders/{gen_purchase_order.po_id}.pdf"
    
    

    return FileResponse(pdf, as_attachment=True, filename=filename)
