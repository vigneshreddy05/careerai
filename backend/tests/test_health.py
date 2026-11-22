from fastapi.testclient import TestClient

try:
    from backend.app.main import app
    from backend.app.core.config import settings
except ModuleNotFoundError:
    from app.main import app
    from app.core.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Verify that the root endpoint returns HTTP 200 and expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["status"] == "online"
    assert data["version"] == settings.APP_VERSION
    assert "docs_url" in data


def test_health_endpoint():
    """Verify that the health check endpoint returns HTTP 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
