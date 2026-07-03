import logging

import pytest

from app.jobs import heartbeat


def test_heartbeat_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="argus.worker"):
        heartbeat()
    assert "heartbeat" in caplog.text
