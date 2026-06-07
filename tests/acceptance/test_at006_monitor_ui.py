"""AT-006 — Monitor UI served from FastAPI."""

from __future__ import annotations

from csmp_monitor.app import UI_STATIC_DIR, create_app


def test_ui_static_dir_exists():
    assert UI_STATIC_DIR.is_dir()


def test_app_root_redirects_to_ui(monitor_client):
    client, _repo = monitor_client
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/app/"


def test_app_serves_index_html(monitor_client):
    client, _repo = monitor_client
    response = client.get("/app/")
    assert response.status_code == 200
    assert "Monitor de Semáforos" in response.text
    assert "leaflet" in response.text.lower()


def test_app_serves_js_and_css(monitor_client):
    client, _repo = monitor_client
    assert client.get("/app/app.js").status_code == 200
    assert client.get("/app/styles.css").status_code == 200
