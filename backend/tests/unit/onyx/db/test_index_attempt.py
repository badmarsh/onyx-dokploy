from datetime import datetime
from datetime import timezone
from types import SimpleNamespace

from onyx.db.enums import IndexingStatus
from onyx.db.index_attempt import mark_attempt_canceled
from onyx.db.index_attempt import resolve_cancellation_reason


def test_resolve_cancellation_reason_prefers_specific_reason() -> None:
    assert (
        resolve_cancellation_reason(
            existing_error_msg="Embedding model failed",
            reason="Task not in queue",
        )
        == "Task not in queue"
    )


def test_resolve_cancellation_reason_preserves_existing_error() -> None:
    assert (
        resolve_cancellation_reason(
            existing_error_msg="Embedding model failed",
            reason="Unknown",
        )
        == "Embedding model failed"
    )


def test_resolve_cancellation_reason_falls_back_to_unknown() -> None:
    assert resolve_cancellation_reason(existing_error_msg=None, reason=None) == "Unknown"


class _FakeResult:
    def __init__(self, attempt: SimpleNamespace) -> None:
        self._attempt = attempt

    def scalar_one(self) -> SimpleNamespace:
        return self._attempt


class _FakeSession:
    def __init__(self, attempt: SimpleNamespace) -> None:
        self.attempt = attempt
        self.committed = False
        self.rolled_back = False

    def execute(self, stmt: object) -> _FakeResult:
        return _FakeResult(self.attempt)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_mark_attempt_canceled_does_not_override_failed_status() -> None:
    attempt = SimpleNamespace(
        id=123,
        status=IndexingStatus.FAILED,
        error_msg="Embedding model failed to process batch",
        connector_credential_pair_id=456,
        time_started=datetime.now(timezone.utc),
    )
    session = _FakeSession(attempt)

    original_optional_telemetry = mark_attempt_canceled.__globals__["optional_telemetry"]
    mark_attempt_canceled.__globals__["optional_telemetry"] = lambda **kwargs: None
    try:
        mark_attempt_canceled(
            index_attempt_id=123,
            db_session=session,
            reason="Index attempt 123 was canceled",
        )
    finally:
        mark_attempt_canceled.__globals__["optional_telemetry"] = (
            original_optional_telemetry
        )

    assert attempt.status == IndexingStatus.FAILED
    assert attempt.error_msg == "Embedding model failed to process batch"
    assert session.committed is False
