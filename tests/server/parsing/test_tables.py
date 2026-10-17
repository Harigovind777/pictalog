import json
from datetime import date, datetime

import pytest

from pictalog.parsing.cells import clean_cell
from pictalog.parsing.detect import UnsupportedFile, detect_kind
from pictalog.parsing.tables import extract_text, read_tables


def test_detect_kind():
    assert detect_kind("x.XLSX") == "spreadsheet"
    assert detect_kind("prices.ods") == "spreadsheet"
    assert detect_kind("a.tsv") == "csv"
    assert detect_kind("a.heic") == "image"
    assert detect_kind("notes.md") == "text"
    with pytest.raises(UnsupportedFile, match=r"\.docx"):
        detect_kind("a.doc")
    with pytest.raises(UnsupportedFile, match=r"\.xlsx"):
        detect_kind("a.exe")


def test_clean_cell():
    assert clean_cell(None) == ""
    assert clean_cell(float("nan")) == ""
    assert clean_cell(499.0) == "499"
    assert clean_cell(4.5) == "4.5"
    assert clean_cell(date(2026, 1, 5)) == "2026-01-05"
    assert clean_cell(datetime(2026, 1, 5, 0, 0)) == "2026-01-05"
    assert clean_cell("  Tee \n") == "Tee"


def test_xlsx_all_sheets(xlsx_two_sheets):
    tables = read_tables("spreadsheet", xlsx_two_sheets)
    assert len(tables) == 2
    assert tables[0] == [["Name", "Price", "Launched"], ["Tee", "499", "2026-01-05"]]
    assert tables[1] == [["Item", "MRP"], ["Mug", "199"]]


def test_csv_semicolon_latin1():
    data = "Name;Price\nCafé crème;4,50\n".encode("latin-1")
    assert read_tables("csv", data) == [[["Name", "Price"], ["Café crème", "4,50"]]]


def test_csv_utf8_bom():
    data = "﻿Name,Price\nMug,199\n".encode("utf-8")
    assert read_tables("csv", data)[0][0] == ["Name", "Price"]


def test_tsv():
    assert read_tables("csv", b"Name\tPrice\nMug\t199\n") == [[["Name", "Price"], ["Mug", "199"]]]


def test_json_nested_list():
    data = json.dumps({"products": [{"name": "Mug", "price": 5}, {"name": "Cup", "size": "S"}]}).encode()
    assert read_tables("json", data) == [[["name", "price", "size"], ["Mug", "5", ""], ["Cup", "", "S"]]]


def test_json_without_product_list():
    assert read_tables("json", b'{"hello": "world"}') == []


def test_docx_table_and_text(docx_table_and_text):
    assert read_tables("docx", docx_table_and_text) == [[["Name", "Price"], ["Bowl", "250"], ["Plate", "300"]]]
    text = extract_text("docx", docx_table_and_text)
    assert "spring range of handmade ceramics" in text
    assert "Plate" in text


def test_pdf_table_merged_across_pages(pdf_table_two_pages):
    tables = read_tables("pdf", pdf_table_two_pages)
    assert len(tables) == 1
    table = tables[0]
    assert table[0] == ["Name", "Price", "Size"]
    assert len(table) == 81
    assert table[-1] == ["Product 79", "179", "M"]
    assert "Product 42" in extract_text("pdf", pdf_table_two_pages)


def test_text_and_image_have_no_tables():
    assert read_tables("text", b"Mug 199") == []
    assert read_tables("image", b"\x89PNG") == []
    assert extract_text("text", "Café".encode("utf-8")) == "Café"
    assert extract_text("image", b"\x89PNG") == ""
