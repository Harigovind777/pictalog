def _signup(client, email="A@X.com", password="password123"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": password, "company_name": "Acme"},
    )


def test_signup_returns_token_and_user(client):
    r = _signup(client)
    assert r.status_code == 201
    body = r.json()
    assert body["token"]
    assert body["user"]["email"] == "a@x.com"
    assert body["user"]["company_name"] == "Acme"
    assert body["user"]["logo_url"] is None


def test_duplicate_email_409(client):
    assert _signup(client).status_code == 201
    assert _signup(client, email="a@x.com").status_code == 409


def test_short_password_422(client):
    assert _signup(client, password="short").status_code == 422


def test_login_wrong_password_401(client):
    _signup(client)
    r = client.post("/api/auth/login", json={"email": "a@x.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_login_then_me(client):
    _signup(client)
    r = client.post("/api/auth/login", json={"email": "a@x.com", "password": "password123"})
    assert r.status_code == 200
    token = r.json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@x.com"


def test_me_without_token_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_garbage_token_401(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert r.status_code == 401


def test_update_company_name(client, signup):
    headers = signup()
    r = client.patch("/api/auth/me", json={"company_name": "Acme Ltd"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["company_name"] == "Acme Ltd"
