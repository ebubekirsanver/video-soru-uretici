import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FRONTEND = "http://localhost:3000"


def test_allowed_origin_gets_cors_header():
    r = client.get("/health", headers={"Origin": FRONTEND})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == FRONTEND


def test_preflight_for_post_from_frontend():
    # Tarayıcı JSON gövdeli POST'tan önce OPTIONS ile izin sorar
    r = client.options(
        "/api/questions",
        headers={
            "Origin": FRONTEND,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == FRONTEND
    assert "POST" in r.headers["access-control-allow-methods"]


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3001",  # başka port
        "http://127.0.0.1:3000",  # aynı makine ama farklı kaynak adı
        "https://localhost:3000",  # farklı şema
        "http://example.com",
    ],
)
def test_other_origins_are_not_allowed(origin):
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 200  # istek yanıtlanır ama tarayıcı izin başlığı görmez
    assert "access-control-allow-origin" not in r.headers


def test_preflight_from_other_origin_is_rejected():
    r = client.options(
        "/api/questions",
        headers={"Origin": "http://example.com", "Access-Control-Request-Method": "POST"},
    )
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_credentials_not_allowed():
    r = client.get("/health", headers={"Origin": FRONTEND})
    assert "access-control-allow-credentials" not in r.headers
