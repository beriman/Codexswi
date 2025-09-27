from fastapi.testclient import TestClient

from app.main import app


def test_homepage_returns_success():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Sensasiwangi" in response.text
