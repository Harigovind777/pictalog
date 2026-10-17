import pytest
from fastapi.testclient import TestClient

from pictalog.config import Settings
from pictalog.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite:///{tmp_path}/test.db", storage_dir=tmp_path / "files")


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def signup(client):
    """Returns a function that creates an account and gives back its auth headers."""

    def _signup(email: str = "a@x.com", company: str = "Acme") -> dict[str, str]:
        r = client.post(
            "/api/auth/signup",
            json={"email": email, "password": "password123", "company_name": company},
        )
        assert r.status_code == 201, r.text
        return {"Authorization": f"Bearer {r.json()['token']}"}

    return _signup
