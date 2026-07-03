import logging

import pytest

from app import jobs


def test_heartbeat_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="argus.worker"):
        jobs.heartbeat()
    assert "heartbeat" in caplog.text


def test_market_snapshot_runs_collector(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    async def fake_collect() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(jobs, "collect_market", fake_collect)
    jobs.market_snapshot()
    assert called
