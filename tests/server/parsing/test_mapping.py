from pictalog.parsing.mapping import find_table, map_columns


def test_map_columns_synonyms():
    assert map_columns(["Item Code", "Product Name", "MRP (₹)", "Colour", "Remarks"]) == {
        "Item Code": "sku",
        "Product Name": "name",
        "MRP (₹)": "price",
        "Colour": "colour",
        "Remarks": None,
    }


def test_map_columns_contains_whole_words():
    assert map_columns(["Selling Price (INR)", "Fabric Type", "Image Link"]) == {
        "Selling Price (INR)": "price",
        "Fabric Type": "material",
        "Image Link": "image_url",
    }


def test_map_columns_first_wins():
    assert map_columns(["Price", "Cost"]) == {"Price": "price", "Cost": None}


def test_map_columns_blank_header():
    assert map_columns(["", "Name"]) == {"": None, "Name": "name"}


def test_find_table_skips_title_rows():
    table = [
        ["ACME Pvt Ltd Catalogue 2026", "", ""],
        ["", "", ""],
        ["Name", "Price", "Size"],
        ["Mug", "199", "350 ml"],
        ["", "", ""],
    ]
    match = find_table([table])
    assert match is not None
    assert match.headers == ["Name", "Price", "Size"]
    assert match.rows == [["Mug", "199", "350 ml"]]
    assert match.mapping == {"Name": "name", "Price": "price", "Size": "size"}


def test_find_table_picks_best_table():
    notes = [["Name", "Notes"], ["x", "y"]]
    products = [["Product", "SKU", "Price", "Colour"], ["Tee", "T1", "499", "Red"]]
    match = find_table([notes, products])
    assert match.headers == ["Product", "SKU", "Price", "Colour"]


def test_find_table_none_when_no_header():
    assert find_table([[["hello", "world"]]]) is None
    assert find_table([[["Price", "Size"], ["1", "2"]]]) is None  # needs name or description
    assert find_table([]) is None


def test_find_table_pads_short_rows():
    match = find_table([[["Name", "Price", "Size"], ["Mug", "199"]]])
    assert match.rows == [["Mug", "199", ""]]


def test_find_table_makes_headers_unique():
    match = find_table([[["Name", "Price", "Price", ""], ["Mug", "1", "2", "x"]]])
    assert match.headers == ["Name", "Price", "Price (2)", "Column 4"]
    assert match.mapping == {"Name": "name", "Price": "price", "Price (2)": None, "Column 4": None}
