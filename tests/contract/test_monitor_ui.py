"""Phase 6: Monitor UI static assets (pt-BR, Leaflet, bottleneck highlights)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "services" / "monitor-ui" / "static"


def test_ui_static_files_exist():
    assert (UI_DIR / "index.html").is_file()
    assert (UI_DIR / "app.js").is_file()
    assert (UI_DIR / "styles.css").is_file()


def test_ui_copy_is_pt_br():
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    assert 'lang="pt-BR"' in html
    assert "Monitor de Semáforos" in html
    assert "Somente gargalos severos" in html


def test_ui_consumes_monitor_api():
    js = (UI_DIR / "app.js").read_text(encoding="utf-8")
    assert 'fetch("/health")' in js
    assert 'fetch(`/intersections${query}`)' in js or 'fetch(`/intersections' in js


def test_ui_bottleneck_highlight_styles():
    css = (UI_DIR / "styles.css").read_text(encoding="utf-8")
    assert "bottleneck-pulse" in css
    assert ".signal-marker.bottleneck" in css


def test_ui_signal_labels_pt_br():
    js = (UI_DIR / "app.js").read_text(encoding="utf-8")
    assert "Verde" in js
    assert "Vermelho" in js
    assert "Gargalo severo" in js
