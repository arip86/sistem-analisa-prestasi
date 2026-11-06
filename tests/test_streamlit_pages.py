from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from config import settings
from database.connection import database_ready

pytestmark = pytest.mark.skipif(
    not settings.is_configured() or not database_ready(),
    reason="Database belum dikonfigurasi atau tabel belum dibuat.",
)


def _analysis_page() -> None:
    from views import analysis_view

    analysis_view.render()


def _dashboard_page() -> None:
    from views import dashboard

    dashboard.render()


def _full_app() -> None:
    import app

    app.main()


def test_analysis_page_renders_all_tabs():
    app = AppTest.from_function(_analysis_page).run(timeout=90)
    assert not app.exception, app.exception
    assert app.tabs
    assert any("Analisis Data" in item.value for item in app.markdown)


def test_dashboard_page_renders():
    app = AppTest.from_function(_dashboard_page).run(timeout=90)
    assert not app.exception, app.exception
    assert any("Dasbor Prestasi Mahasiswa" in item.value for item in app.markdown)


def test_public_mode_hides_import_menu(monkeypatch):
    from components.data_access import clear_caches

    monkeypatch.setattr(settings, "PUBLIC_READ_ONLY", True)
    clear_caches()
    app = AppTest.from_function(_full_app).run(timeout=90)
    assert not app.exception, app.exception
    navigation = app.radio[0]
    assert "Impor Data" not in navigation.options
    assert "Tentang" in navigation.options
