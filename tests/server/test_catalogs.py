from test_images import png_bytes


def test_create_and_list_catalogs(client, signup):
    h = signup()
    r = client.post("/api/catalogs", json={"name": "Summer", "currency": "₹"}, headers=h)
    assert r.status_code == 201
    created = r.json()
    assert created["name"] == "Summer" and created["currency"] == "₹"
    assert created["products"] == [] and created["share_enabled"] is False

    listing = client.get("/api/catalogs", headers=h).json()
    assert len(listing) == 1
    assert listing[0]["name"] == "Summer"
    assert listing[0]["product_count"] == 0 and listing[0]["variant_count"] == 0


def test_update_catalog(client, signup):
    h = signup()
    cid = client.post("/api/catalogs", json={"name": "Summer"}, headers=h).json()["id"]
    r = client.patch(f"/api/catalogs/{cid}", json={"name": "Winter", "currency": "$"}, headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "Winter" and r.json()["currency"] == "$"


def test_other_company_gets_404(client, signup):
    a = signup("a@x.com")
    b = signup("b@x.com", company="Other")
    cid = client.post("/api/catalogs", json={"name": "Summer"}, headers=a).json()["id"]
    assert client.get(f"/api/catalogs/{cid}", headers=b).status_code == 404
    assert client.patch(f"/api/catalogs/{cid}", json={"name": "x"}, headers=b).status_code == 404
    assert client.delete(f"/api/catalogs/{cid}", headers=b).status_code == 404
    assert client.get("/api/catalogs", headers=b).json() == []
    assert client.get(f"/api/catalogs/{cid}", headers=a).status_code == 200


def test_delete_catalog_removes_it(client, signup):
    h = signup()
    cid = client.post("/api/catalogs", json={"name": "Summer"}, headers=h).json()["id"]
    assert client.delete(f"/api/catalogs/{cid}", headers=h).status_code == 204
    assert client.get(f"/api/catalogs/{cid}", headers=h).status_code == 404


def test_catalogs_need_login(client):
    assert client.get("/api/catalogs").status_code == 401


def test_logo_upload_sets_logo_url(client, signup):
    h = signup()
    r = client.post("/api/auth/me/logo", files={"file": ("logo.png", png_bytes(300, 100), "image/png")}, headers=h)
    assert r.status_code == 200
    logo_url = r.json()["logo_url"]
    assert logo_url.startswith("/api/files/img/")
    assert client.get("/api/auth/me", headers=h).json()["logo_url"] == logo_url
    img = client.get(logo_url)
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/webp"


def test_logo_upload_rejects_non_image(client, signup):
    h = signup()
    r = client.post("/api/auth/me/logo", files={"file": ("logo.png", b"not an image", "image/png")}, headers=h)
    assert r.status_code == 400


def test_files_rejects_non_img_keys(client, app):
    app.state.storage.save("uploads/secret.xlsx", b"data", "application/octet-stream")
    assert client.get("/api/files/uploads/secret.xlsx").status_code == 404
    assert client.get("/api/files/img/../uploads/secret.xlsx").status_code == 404
    assert client.get("/api/files/img/missing.webp").status_code == 404


def test_delete_catalog_cancels_its_jobs(client, signup, db):
    from sqlalchemy import select

    from pictalog.models import Job
    from test_worker_api import applied_catalog

    h = signup()
    catalog = applied_catalog(client, h)
    assert db.scalars(select(Job.status)).all() == ["queued"] * 3
    client.delete(f"/api/catalogs/{catalog['id']}", headers=h)
    db.expire_all()
    assert set(db.scalars(select(Job.status)).all()) == {"cancelled"}
