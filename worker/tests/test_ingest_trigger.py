import pytest

from app import jobs


def test_check_ingest_request_runs_when_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    ran = False

    async def fake_pop() -> str | None:
        return "2026-07-11T00:00:00+00:00"

    async def fake_ingest() -> int:
        nonlocal ran
        ran = True
        return 0

    monkeypatch.setattr("argus_core.cache.pop_ingest_request", fake_pop)
    monkeypatch.setattr("app.ingest.run_ingestion", fake_ingest)
    jobs.check_ingest_request()
    assert ran


def test_check_ingest_request_noop_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    ran = False

    async def fake_pop() -> str | None:
        return None

    async def fake_ingest() -> int:
        nonlocal ran
        ran = True
        return 0

    monkeypatch.setattr("argus_core.cache.pop_ingest_request", fake_pop)
    monkeypatch.setattr("app.ingest.run_ingestion", fake_ingest)
    jobs.check_ingest_request()
    assert not ran
