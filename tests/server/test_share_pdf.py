import io

import pdfplumber

from pictalog.catalog.sync import apply_items
from pictalog.pdf import render_catalog_pdf
from pictalog.schemas import ExtractedItem as Item
from test_images import png_bytes
from test_imports import XLSX, new_catalog, upload, xlsx
from test_worker_api import W

ROWS = [["Name", "Size", "Price", "SKU"], ["Tee", "S", "₹499", "T1"], ["Tee", "M", "₹499", "T2"], ["Mug", "", "199", "M1"], ["", "", "50", "A1234"]]


def setup_catalog(client, h) -> dict:
    cid = new_catalog(client, h)
    client.patch(f"/api/catalogs/{cid}", json={"currency": "₹"}, headers=h)
    imp = upload(client, h, cid, "c.xlsx", xlsx(ROWS), XLSX).json()
    return client.post(f"/api/imports/{imp['id']}/apply", json={"items": imp["items"]}, headers=h).json()


def pdf_text(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def test_share_toggle_and_public_view(client, signup):
    h = signup(company="Acme Traders")
    catalog = setup_catalog(client, h)
    r = client.post(f"/api/catalogs/{catalog['id']}/share", json={"enabled": True}, headers=h)
    assert r.status_code == 200
    token = r.json()["share_token"]
    assert r.json()["share_enabled"] is True and len(token) >= 16
    public = client.get(f"/api/public/{token}")
    assert public.status_code == 200
    body = public.json()
    assert body["company_name"] == "Acme Traders" and body["name"] == "Spring"
    assert "share_token" not in body
    assert [p["name"] for p in body["products"]][:2] == ["Tee", "Mug"]


def test_public_404_when_disabled_and_token_kept(client, signup):
    h = signup()
    catalog = setup_catalog(client, h)
    token = client.post(f"/api/catalogs/{catalog['id']}/share", json={"enabled": True}, headers=h).json()["share_token"]
    off = client.post(f"/api/catalogs/{catalog['id']}/share", json={"enabled": False}, headers=h).json()
    assert off == {"share_enabled": False, "share_token": token}
    assert client.get(f"/api/public/{token}").status_code == 404
    assert client.get(f"/api/public/{token}/pdf").status_code == 404
    assert client.get("/api/public/not-a-token").status_code == 404
    again = client.post(f"/api/catalogs/{catalog['id']}/share", json={"enabled": True}, headers=h).json()
    assert again["share_token"] == token


def test_share_other_company_404(client, signup):
    a, b = signup("a@x.com"), signup("b@x.com")
    catalog = setup_catalog(client, a)
    assert client.post(f"/api/catalogs/{catalog['id']}/share", json={"enabled": True}, headers=b).status_code == 404
    assert client.get(f"/api/catalogs/{catalog['id']}/pdf", headers=b).status_code == 404


def test_pdf_has_one_cell_per_variant(client, signup):
    h = signup(company="Acme Traders")
    catalog = setup_catalog(client, h)
    job = client.post("/api/worker/claim", json={}, headers=W).json()
    client.post(f"/api/worker/jobs/{job['id']}/image", files={"file": ("a.png", png_bytes(300, 300), "image/png")}, headers=W)
    r = client.get(f"/api/catalogs/{catalog['id']}/pdf", headers=h)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"] == 'attachment; filename="Spring.pdf"'
    text = pdf_text(r.content)
    assert "Acme Traders" in text and "Spring" in text
    assert text.count("Tee") >= 2 and "Mug" in text and "A1234" in text
    assert "Size S" in text and "Size M" in text
    assert "₹499" in text
    assert "₹199" in text  # currency added when the sheet wrote just a number
    assert "No image" in text


def test_public_pdf(client, signup):
    h = signup()
    catalog = setup_catalog(client, h)
    token = client.post(f"/api/catalogs/{catalog['id']}/share", json={"enabled": True}, headers=h).json()["share_token"]
    r = client.get(f"/api/public/{token}/pdf")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


def test_pdf_survives_broken_image_url(db, catalog, app):
    apply_items(db, catalog, [Item(name="Mug", image_url="https://example.invalid/mug.jpg")])

    def broken_fetch(url, timeout):
        raise OSError("network down")

    data = render_catalog_pdf(catalog, catalog.user, app.state.storage, fetch=broken_fetch)
    assert data.startswith(b"%PDF")
    assert "No image" in pdf_text(data)


def test_pdf_empty_catalog(db, catalog, app):
    data = render_catalog_pdf(catalog, catalog.user, app.state.storage)
    assert "This catalog has no products yet" in pdf_text(data)
