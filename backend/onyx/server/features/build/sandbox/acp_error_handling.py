"""Helpers for turning ACP edge cases into actionable error events."""

from typing import Any

from acp.schema import Error


EMPTY_AGENT_RESPONSE_MESSAGE = (
    "The coding agent returned an empty response before starting work. "
    "This usually indicates a model/provider issue such as exhausted credits, "
    "authentication failure, or a token limit."
)

SESSION_ERROR_MESSAGE = "The coding agent failed before returning any output."


def build_empty_prompt_response_error(payload: dict[str, Any]) -> Error:
    """Create a consistent ACP error for empty successful completions."""
    return Error(code=-1, message=EMPTY_AGENT_RESPONSE_MESSAGE, data=payload)


def extract_session_error_event(message_data: dict[str, Any]) -> Error | None:
    """Convert session-level ACP error notifications into ACP Error events."""
    method = message_data.get("method")
    if method in ("session/error", "session.error"):
        params = message_data.get("params")
        if isinstance(params, dict):
            return _coerce_error_event(params)
        return None

    if method != "session/update":
        return None

    params = message_data.get("params")
    if not isinstance(params, dict):
        return None

    update = params.get("update")
    if not isinstance(update, dict):
        return None

    update_type = update.get("sessionUpdate")
    if update_type not in ("error", "session_error"):
        return None

    return _coerce_error_event(update)


def should_treat_prompt_response_as_error(
    payload: dict[str, Any],
    prior_events_yielded: int,
    *,
    ignored_keys: set[str] | None = None,
) -> bool:
    """Detect prompt completions that ended without any agent output."""
    if prior_events_yielded != 0:
        return False

    if payload.get("stopReason") != "end_turn":
        return False

    usage = payload.get("usage")
    if isinstance(usage, dict):
        total_tokens = usage.get("totalTokens")
        if isinstance(total_tokens, int) and total_tokens > 0:
            return False

    allowed_keys = {"_meta", "stopReason", "usage"}
    if ignored_keys:
        allowed_keys.update(ignored_keys)

    return all(key in allowed_keys for key in payload)


def _coerce_error_event(payload: dict[str, Any]) -> Error:
    normalized_payload = payload.get("properties")
    if not isinstance(normalized_payload, dict):
        normalized_payload = payload

    nested_error = normalized_payload.get("error")
    if not isinstance(nested_error, dict):
        nested_error = {}

    nested_data = nested_error.get("data")
    if not isinstance(nested_data, dict):
        nested_data = {}

    message = _first_non_empty_string(
        normalized_payload.get("message"),
        nested_error.get("message"),
        nested_data.get("message"),
        normalized_payload.get("detail"),
        nested_data.get("responseBody"),
    )
    if message is None:
        message = SESSION_ERROR_MESSAGE

    code = _coerce_error_code(
        normalized_payload.get("code"),
        nested_error.get("code"),
        nested_data.get("statusCode"),
    )

    data: Any = nested_error or normalized_payload
    return Error(code=code, message=message, data=data)


def _coerce_error_code(*values: Any) -> int:
    for value in values:
        if isinstance(value, int):
            return value
    return -1


def _first_non_empty_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None
