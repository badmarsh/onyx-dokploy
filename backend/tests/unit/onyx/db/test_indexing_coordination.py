from types import SimpleNamespace

from onyx.db.indexing_coordination import IndexingCoordination


class _FakeSession:
    def __init__(self) -> None:
        self.committed = False

    def commit(self) -> None:
        self.committed = True


def test_request_cancellation_sets_flag_and_reason() -> None:
    session = _FakeSession()
    attempt = SimpleNamespace(cancellation_requested=False, error_msg=None)

    original = IndexingCoordination.request_cancellation.__globals__["get_index_attempt"]
    IndexingCoordination.request_cancellation.__globals__["get_index_attempt"] = (
        lambda db_session, index_attempt_id: attempt
    )
    try:
        IndexingCoordination.request_cancellation(
            session, 123, reason="Connector paused by user"
        )
    finally:
        IndexingCoordination.request_cancellation.__globals__["get_index_attempt"] = (
            original
        )

    assert attempt.cancellation_requested is True
    assert attempt.error_msg == "Connector paused by user"
    assert session.committed is True
