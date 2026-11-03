import pytest

from app.settings import ROOT
from scripts.run_demo import build_environment, services


def test_environment_exposes_project_root_and_mock_mode() -> None:
    environment = build_environment(real=False)
    assert environment["PYTHONPATH"] == str(ROOT)
    assert environment["LLM_MODE"] == "mock"
    assert environment["API_URL"] == "http://localhost:8000"


def test_real_mode_does_not_force_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "real")
    assert build_environment(real=True)["LLM_MODE"] == "real"


def test_three_services_with_distinct_health_urls() -> None:
    listed = services()
    assert [service.name for service in listed] == ["api", "chat", "dashboard"]
    assert len({service.health_url for service in listed}) == 3
