from types import SimpleNamespace
from uuid import uuid4

from onyx.server.query_and_chat import chat_backend


def test_get_llm_for_chat_session_naming_uses_session_persona(
    monkeypatch: object,
) -> None:
    chat_session_id = uuid4()
    user = SimpleNamespace(id=uuid4())
    db_session = object()
    request = SimpleNamespace(headers={"authorization": "Bearer token"})
    persona = SimpleNamespace(llm_model_provider_override="private-provider")
    chat_session = SimpleNamespace(persona=persona)
    extracted_headers = {"authorization": "Bearer token"}
    expected_llm = object()

    monkeypatch.setattr(
        chat_backend,
        "get_chat_session_by_id",
        lambda chat_session_id, user_id, db_session: chat_session,
    )
    monkeypatch.setattr(
        chat_backend,
        "extract_headers",
        lambda headers, allowed_headers: extracted_headers,
    )

    def fake_get_llm_for_persona(
        persona: object,
        user: object,
        additional_headers: dict[str, str] | None = None,
    ) -> object:
        assert persona is chat_session.persona
        assert additional_headers == extracted_headers
        assert user is not None
        return expected_llm

    monkeypatch.setattr(chat_backend, "get_llm_for_persona", fake_get_llm_for_persona)

    llm = chat_backend._get_llm_for_chat_session_naming(
        chat_session_id=chat_session_id,
        request=request,
        user=user,
        db_session=db_session,
    )

    assert llm is expected_llm


def test_get_llm_for_chat_session_naming_preserves_default_fallback(
    monkeypatch: object,
) -> None:
    user = SimpleNamespace(id=uuid4())
    request = SimpleNamespace(headers={})
    chat_session = SimpleNamespace(persona=None)
    expected_llm = object()

    monkeypatch.setattr(
        chat_backend,
        "get_chat_session_by_id",
        lambda chat_session_id, user_id, db_session: chat_session,
    )
    monkeypatch.setattr(
        chat_backend,
        "extract_headers",
        lambda headers, allowed_headers: {},
    )

    def fake_get_llm_for_persona(
        persona: object,
        user: object,
        additional_headers: dict[str, str] | None = None,
    ) -> object:
        assert persona is None
        return expected_llm

    monkeypatch.setattr(chat_backend, "get_llm_for_persona", fake_get_llm_for_persona)

    llm = chat_backend._get_llm_for_chat_session_naming(
        chat_session_id=uuid4(),
        request=request,
        user=user,
        db_session=object(),
    )

    assert llm is expected_llm
