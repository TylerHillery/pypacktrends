import json
from typing import Any, cast
from urllib.request import Request

import pytest

from app.analytics.posthog import capture_package_requested_events
from app.core.config import settings


class DummyResponse:
    def __enter__(self) -> "DummyResponse":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None


@pytest.mark.parametrize(
    ("enabled", "api_key", "packages"),
    [
        (False, "test_api_key", ["duckdb"]),
        (True, None, ["duckdb"]),
        (True, "test_api_key", []),
    ],
)
def test_capture_package_requested_events_noop(
    monkeypatch: pytest.MonkeyPatch,
    enabled: bool,
    api_key: str | None,
    packages: list[str],
) -> None:
    monkeypatch.setattr(settings, "ENABLE_SERVER_ANALYTICS", enabled)
    monkeypatch.setattr(settings, "POSTHOG_API_KEY", api_key)

    calls = 0

    def fake_urlopen(*args: Any, **kwargs: Any) -> DummyResponse:
        nonlocal calls
        calls += 1
        return DummyResponse()

    monkeypatch.setattr("app.analytics.posthog.urlopen", fake_urlopen)

    capture_package_requested_events(
        packages=packages,
        time_range="3months",
        show_percentage=False,
        hx_trigger="dataRefresh",
    )

    assert calls == 0


def test_capture_package_requested_events_emits_one_per_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENABLE_SERVER_ANALYTICS", True)
    monkeypatch.setattr(settings, "POSTHOG_API_KEY", "test_api_key")
    monkeypatch.setattr(settings, "POSTHOG_HOST", "https://us.i.posthog.com")

    request_payloads: list[dict[str, Any]] = []
    request_urls: list[str] = []

    def fake_urlopen(request: Request, timeout: int) -> DummyResponse:
        request_urls.append(request.full_url)
        data = cast(bytes, request.data)
        request_payloads.append(json.loads(data.decode("utf-8")))
        assert timeout == 2
        return DummyResponse()

    monkeypatch.setattr("app.analytics.posthog.urlopen", fake_urlopen)

    capture_package_requested_events(
        packages=["pandas", "duckdb"],
        time_range="3months",
        show_percentage=True,
        hx_trigger="dataRefresh",
        request_id="req-123",
    )

    assert len(request_payloads) == 2
    assert all(url == "https://us.i.posthog.com/capture/" for url in request_urls)

    first_payload = request_payloads[0]
    assert first_payload["event"] == "package_requested"
    assert first_payload["api_key"] == "test_api_key"
    assert first_payload["distinct_id"] == "server"
    assert first_payload["properties"]["package"] == "duckdb"
    assert first_payload["properties"]["packages"] == ["duckdb", "pandas"]
    assert first_payload["properties"]["time_range"] == "3months"
    assert first_payload["properties"]["show_percentage"] is True
    assert first_payload["properties"]["hx_trigger"] == "dataRefresh"
    assert first_payload["properties"]["request_id"] == "req-123"
    assert first_payload["properties"]["source"] == "server_htmx"

    second_payload = request_payloads[1]
    assert second_payload["properties"]["package"] == "pandas"
    assert second_payload["properties"]["packages"] == ["duckdb", "pandas"]
    assert second_payload["properties"]["request_id"] == "req-123"
