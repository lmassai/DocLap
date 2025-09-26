import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def get_page_dimensions(pdf_path, page_num=0):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        page = pdf_reader.pages[page_num]
        width = page.mediabox.width
        height = page.mediabox.height
        return width, height

def draw_bounding_boxes(canvas, page_width, page_height, bbox_list, element_kind, color):
    page_num = bbox_list[0]
    x = bbox_list[1]
    y = bbox_list[2]
    w = bbox_list[3]
    h = bbox_list[4]
    canvas.setStrokeColorRGB(*color)
    if element_kind != 'phrase' and element_kind != 'Abstract' and element_kind != 'Reference' and element_kind != 'p':
        canvas.setFont("Helvetica", 10)
        canvas.drawString(x, float(page_height) - y, element_kind + ' at page ' + str(page_num))
    canvas.rect(x, float(page_height) - y - h, w, h)

def create_pdf_with_bounding_boxes(pdf_path, output_pdf_path, page_width, page_height, bbox_lists, element_kind, color):
    c = canvas.Canvas(output_pdf_path, pagesize=(page_width, page_height))
    processed_pages = set()
    current_page = 1
    total_pages = len(PdfReader(pdf_path).pages)

    for bbox in bbox_lists:
        page_num = bbox[0]

        while current_page is not None and current_page < page_num:
            c.showPage()
            processed_pages.add(current_page)
            current_page += 1

        if current_page is None or current_page != page_num:
            if current_page is not None:
                c.showPage()
            current_page = page_num
            processed_pages.add(current_page)

        draw_bounding_boxes(c, page_width, page_height, bbox, element_kind, color)

    while current_page is not None and current_page <= total_pages:
        if current_page not in processed_pages:
            c.showPage()
            processed_pages.add(current_page)
        current_page += 1

    c.save()

def overlay_pdfs(pdf1_path, pdf2_path, output_path):
    pdf1 = PdfReader(pdf1_path)
    pdf2 = PdfReader(pdf2_path)

    output_pdf = PdfWriter()

    for page_num in range(min(len(pdf1.pages), len(pdf2.pages))):
        page1 = pdf1.pages[page_num]
        page2 = pdf2.pages[page_num]

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.showPage()
        can.save()

        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        overlay_page.merge_page(page1)
        overlay_page.merge_page(page2)

        output_pdf.add_page(overlay_page)

    with open(output_path, 'wb') as output_file:
        output_pdf.write(output_file)
