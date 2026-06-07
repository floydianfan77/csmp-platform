"""Unit tests for stream runner drain / idle behaviour."""

from __future__ import annotations

import pytest

from flink_job.stream_runner import should_arm_idle_timer


@pytest.mark.parametrize(
    ("written", "max_messages", "from_earliest", "expected"),
    [
        (0, None, False, False),
        (0, 20, False, True),
        (0, None, True, True),
        (4, None, False, True),
        (4, 20, True, True),
    ],
)
def test_should_arm_idle_timer(written, max_messages, from_earliest, expected):
    assert should_arm_idle_timer(written, max_messages, from_earliest) is expected
