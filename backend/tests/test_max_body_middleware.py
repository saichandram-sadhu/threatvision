"""Max request body middleware (M17)."""

from starlette.testclient import TestClient

from app.config import get_settings
from app.main import create_application


def test_oversized_post_rejected_with_413(monkeypatch) -> None:
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", "65536")
    get_settings.cache_clear()
    try:
        app = create_application()
        client = TestClient(app)
        body = b"x" * 70_000
        res = client.post("/health", content=body, headers={"content-type": "application/octet-stream"})
        assert res.status_code == 413
    finally:
        get_settings.cache_clear()
