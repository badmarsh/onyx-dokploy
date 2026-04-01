import threading
from unittest.mock import Mock

from acp.schema import PromptResponse

import onyx.server.features.build.sandbox.local.agent_client as agent_client_module
from onyx.server.features.build.sandbox.acp_types import SSEKeepalive
from onyx.server.features.build.sandbox.local.agent_client import ACPAgentClient
from onyx.server.features.build.sandbox.local.agent_client import ACPSession


def test_send_message_emits_keepalive_while_waiting(monkeypatch) -> None:
    client = ACPAgentClient(auto_start=False)
    client._state.current_session = ACPSession(  # type: ignore[attr-defined]
        session_id="acp-session",
        cwd="/tmp/session",
    )
    client._read_lock = threading.Lock()  # type: ignore[attr-defined]

    process = Mock()
    process.poll.return_value = None

    messages = iter(
        [
            None,
            {
                "jsonrpc": "2.0",
                "id": 7,
                "result": {
                    "stopReason": "end_turn",
                    "usage": {
                        "totalTokens": 5,
                        "inputTokens": 3,
                        "outputTokens": 2,
                    },
                },
            },
        ]
    )

    monkeypatch.setattr(agent_client_module, "SSE_KEEPALIVE_INTERVAL", 0.0)
    client._ensure_running = Mock(return_value=process)  # type: ignore[method-assign]
    client._send_request = Mock(return_value=7)  # type: ignore[method-assign]
    client._read_message = Mock(side_effect=lambda timeout=None: next(messages))  # type: ignore[method-assign]

    events = list(client.send_message("Build something"))

    assert len(events) == 2
    assert isinstance(events[0], SSEKeepalive)
    assert isinstance(events[1], PromptResponse)
    assert events[1].stop_reason == "end_turn"
