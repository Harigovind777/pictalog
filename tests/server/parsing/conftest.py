import io
from datetime import date

import pytest
from docx import Document
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


@pytest.fixture
def xlsx_two_sheets() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Apparel"
    ws.append(["Name", "Price", "Launched"])
    ws.append(["Tee", 499.0, date(2026, 1, 5)])
    other = wb.create_sheet("Kitchen")
    other.append(["Item", "MRP"])
    other.append(["Mug", 199])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def docx_table_and_text() -> bytes:
    doc = Document()
    doc.add_paragraph("Our spring range of handmade ceramics.")
    table = doc.add_table(rows=3, cols=2)
    for r, row in enumerate([["Name", "Price"], ["Bowl", "250"], ["Plate", "300"]]):
        for c, value in enumerate(row):
            table.cell(r, c).text = value
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def pdf_table_two_pages() -> bytes:
    rows = [["Name", "Price", "Size"]] + [[f"Product {i}", str(100 + i), "M"] for i in range(80)]
    buf = io.BytesIO()
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    SimpleDocTemplate(buf, pagesize=A4).build([table])
    return buf.getvalue()
