from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from unittest.mock import patch

from onyx.db.models import IndexingStatus
from onyx.server.documents.connector import get_currently_failed_indexing_status


def _attempt(
    cc_pair_id: int,
    status: IndexingStatus,
    error_msg: str | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        connector_credential_pair_id=cc_pair_id,
        status=status,
        error_msg=error_msg,
        time_updated=datetime.now(timezone.utc),
    )


def _cc_pair(cc_pair_id: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=cc_pair_id,
        name=name,
        connector_id=cc_pair_id + 100,
        credential_id=cc_pair_id + 200,
    )


def test_failed_indexing_status_only_returns_latest_finished_failures() -> None:
    failed_pair = _cc_pair(1, "Failed Connector")
    canceled_pair = _cc_pair(2, "Canceled Connector")

    with patch(
        "onyx.server.documents.connector.get_latest_index_attempts",
        return_value=[
            _attempt(1, IndexingStatus.FAILED, "Real failure"),
            _attempt(2, IndexingStatus.CANCELED, "Task not in queue"),
        ],
    ), patch(
        "onyx.server.documents.connector.get_connector_credential_pairs_for_user",
        return_value=[failed_pair, canceled_pair],
    ), patch(
        "onyx.server.documents.connector.check_deletion_attempt_is_allowed",
        return_value=False,
    ):
        result = get_currently_failed_indexing_status(
            secondary_index=False,
            user=SimpleNamespace(),
            db_session=SimpleNamespace(),
            get_editable=False,
        )

    assert len(result) == 1
    assert result[0].cc_pair_id == 1
    assert result[0].error_msg == "Real failure"
