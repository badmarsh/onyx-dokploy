from datetime import datetime
from datetime import timezone
from types import SimpleNamespace

from onyx.background.celery.tasks.docprocessing.tasks import (
    monitor_indexing_attempt_progress,
)
from onyx.db.enums import ConnectorCredentialPairStatus
from onyx.db.enums import IndexingStatus
from onyx.db.indexing_coordination import CoordinationStatus


class _FakeTask:
    app = None


def test_monitor_does_not_overwrite_terminal_attempt_with_cancellation() -> None:
    attempt = SimpleNamespace(
        id=123,
        celery_task_id="task-123",
        connector_credential_pair_id=456,
        search_settings_id=789,
        time_created=datetime.now(timezone.utc),
        status=IndexingStatus.IN_PROGRESS,
    )
    cc_pair = SimpleNamespace(status=ConnectorCredentialPairStatus.ACTIVE)
    terminal_attempt = SimpleNamespace(status=IndexingStatus.FAILED)

    module_globals = monitor_indexing_attempt_progress.__globals__

    originals = {
        "get_connector_credential_pair_from_id": module_globals[
            "get_connector_credential_pair_from_id"
        ],
        "get_db_current_time": module_globals["get_db_current_time"],
        "get_index_attempt": module_globals["get_index_attempt"],
        "mark_attempt_canceled": module_globals["mark_attempt_canceled"],
    }

    cancellation_calls: list[int] = []

    module_globals["get_connector_credential_pair_from_id"] = (
        lambda db_session, connector_credential_pair_id: cc_pair
    )
    module_globals["get_db_current_time"] = lambda db_session: datetime.now(
        timezone.utc
    )
    module_globals["get_index_attempt"] = lambda db_session, index_attempt_id: (
        terminal_attempt
    )
    module_globals["mark_attempt_canceled"] = (
        lambda index_attempt_id, db_session, reason: cancellation_calls.append(
            index_attempt_id
        )
    )

    original_get_coordination_status = (
        module_globals["IndexingCoordination"].get_coordination_status
    )
    module_globals["IndexingCoordination"].get_coordination_status = staticmethod(
        lambda db_session, index_attempt_id: CoordinationStatus(
            found=True,
            total_batches=None,
            completed_batches=0,
            total_failures=1,
            total_docs=0,
            total_chunks=0,
            status=IndexingStatus.FAILED,
            cancellation_requested=True,
        )
    )

    try:
        monitor_indexing_attempt_progress(
            attempt=attempt,
            tenant_id="tenant",
            db_session=SimpleNamespace(commit=lambda: None),
            task=_FakeTask(),
        )
    finally:
        module_globals["get_connector_credential_pair_from_id"] = originals[
            "get_connector_credential_pair_from_id"
        ]
        module_globals["get_db_current_time"] = originals["get_db_current_time"]
        module_globals["get_index_attempt"] = originals["get_index_attempt"]
        module_globals["mark_attempt_canceled"] = originals["mark_attempt_canceled"]
        module_globals["IndexingCoordination"].get_coordination_status = (
            original_get_coordination_status
        )

    assert cancellation_calls == []
