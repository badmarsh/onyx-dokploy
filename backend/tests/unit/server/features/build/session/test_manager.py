from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from onyx.db.enums import SandboxStatus
import onyx.server.features.build.session.manager as manager_module
from onyx.server.features.build.session.manager import SessionManager


def test_get_webapp_info_returns_same_origin_proxy_path(
    monkeypatch,
) -> None:
    sandbox_manager = Mock()
    monkeypatch.setattr(
        manager_module, "get_sandbox_manager", lambda: sandbox_manager
    )

    session_id = uuid4()
    user_id = uuid4()
    sandbox_id = uuid4()

    monkeypatch.setattr(
        manager_module,
        "get_build_session",
        lambda *args: SimpleNamespace(nextjs_port=3023, sharing_scope="private"),
    )
    monkeypatch.setattr(
        manager_module,
        "get_sandbox_by_user_id",
        lambda *args: SimpleNamespace(id=sandbox_id, status=SandboxStatus.RUNNING),
    )

    manager = SessionManager(Mock())
    monkeypatch.setattr(manager, "_check_nextjs_ready", lambda *args: True)

    info = manager.get_webapp_info(session_id, user_id)

    assert info == {
        "has_webapp": True,
        "webapp_url": f"/api/build/sessions/{session_id}/webapp",
        "status": "running",
        "ready": True,
        "sharing_scope": "private",
    }
    sandbox_manager.ensure_nextjs_running.assert_not_called()


def test_get_webapp_info_requests_nextjs_restart_when_not_ready(
    monkeypatch,
) -> None:
    sandbox_manager = Mock()
    monkeypatch.setattr(
        manager_module, "get_sandbox_manager", lambda: sandbox_manager
    )

    session_id = uuid4()
    user_id = uuid4()
    sandbox_id = uuid4()

    monkeypatch.setattr(
        manager_module,
        "get_build_session",
        lambda *args: SimpleNamespace(nextjs_port=3023, sharing_scope="private"),
    )
    monkeypatch.setattr(
        manager_module,
        "get_sandbox_by_user_id",
        lambda *args: SimpleNamespace(id=sandbox_id, status=SandboxStatus.RUNNING),
    )

    manager = SessionManager(Mock())
    monkeypatch.setattr(manager, "_check_nextjs_ready", lambda *args: False)

    info = manager.get_webapp_info(session_id, user_id)

    assert info["webapp_url"] == f"/api/build/sessions/{session_id}/webapp"
    assert info["ready"] is False
    sandbox_manager.ensure_nextjs_running.assert_called_once_with(
        sandbox_id, session_id, 3023
    )


def test_get_llm_config_uses_requested_provider_name(monkeypatch) -> None:
    monkeypatch.setattr(manager_module, "get_sandbox_manager", lambda: Mock())
    monkeypatch.setattr(
        manager_module,
        "fetch_llm_provider_for_build_mode",
        lambda *args, **kwargs: SimpleNamespace(
            name="Aliyun DashScope",
            provider="openai",
            api_key="test-key",
            api_base="https://example.com",
            model_configurations=[
                SimpleNamespace(name="qwen3-max-preview", is_visible=True),
            ],
        ),
    )

    manager = SessionManager(Mock())

    config = manager._get_llm_config(
        "Aliyun DashScope",
        "openai",
        "qwen3-max-preview",
    )

    assert config.provider == "openai"
    assert config.model_name == "qwen3-max-preview"
    assert config.api_key == "test-key"
    assert config.api_base == "https://example.com"


def test_get_llm_config_falls_back_to_visible_model_when_requested_model_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(manager_module, "get_sandbox_manager", lambda: Mock())
    monkeypatch.setattr(
        manager_module,
        "fetch_llm_provider_for_build_mode",
        lambda *args, **kwargs: SimpleNamespace(
            name="NVIDIA NIM",
            provider="openai",
            api_key="test-key",
            api_base="https://example.com",
            model_configurations=[
                SimpleNamespace(name="qwen3-coder", is_visible=True),
                SimpleNamespace(name="qwen3-next", is_visible=True),
            ],
        ),
    )

    manager = SessionManager(Mock())

    config = manager._get_llm_config(
        "NVIDIA NIM",
        "openai",
        "gpt-5.2",
    )

    assert config.provider == "openai"
    assert config.model_name == "qwen3-coder"


def test_get_llm_config_falls_back_to_default_when_requested_provider_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(manager_module, "get_sandbox_manager", lambda: Mock())
    monkeypatch.setattr(
        manager_module,
        "fetch_llm_provider_for_build_mode",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        manager_module,
        "fetch_default_llm_model",
        lambda *args, **kwargs: SimpleNamespace(
            name="qwen3-max-preview",
            llm_provider=SimpleNamespace(
                provider="openai",
                api_key=SimpleNamespace(
                    get_value=lambda apply_mask=False: "default-key"
                ),
                api_base="https://default.example.com",
            ),
        ),
    )

    manager = SessionManager(Mock())

    config = manager._get_llm_config(
        "missing-provider",
        "openai",
        "gpt-5.2",
    )

    assert config.provider == "openai"
    assert config.model_name == "qwen3-max-preview"
    assert config.api_key == "default-key"
