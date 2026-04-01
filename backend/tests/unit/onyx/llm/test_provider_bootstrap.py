from onyx.llm.provider_bootstrap import (
    build_static_openai_compatible_provider_request,
)
from onyx.llm.provider_bootstrap import normalize_openai_compatible_api_base


def test_normalize_openai_compatible_api_base_appends_v1() -> None:
    assert (
        normalize_openai_compatible_api_base(
            "https://example.com/functions/v1/uncensoredlm-api"
        )
        == "https://example.com/functions/v1/uncensoredlm-api/v1"
    )


def test_normalize_openai_compatible_api_base_keeps_existing_v1() -> None:
    assert (
        normalize_openai_compatible_api_base(
            "https://example.com/functions/v1/uncensoredlm-api/v1/"
        )
        == "https://example.com/functions/v1/uncensoredlm-api/v1"
    )


def test_build_static_openai_compatible_provider_request() -> None:
    request = build_static_openai_compatible_provider_request(
        name="Uncensored LM",
        api_key="secret",
        api_base="https://example.com/functions/v1/uncensoredlm-api",
        model_name="uncensored-lm",
        existing_id=12,
    )

    assert request.id == 12
    assert request.name == "Uncensored LM"
    assert request.provider == "openai"
    assert request.api_key == "secret"
    assert request.api_base == "https://example.com/functions/v1/uncensoredlm-api/v1"
    assert request.is_auto_mode is False
    assert request.api_key_changed is True
    assert len(request.model_configurations) == 1
    assert request.model_configurations[0].name == "uncensored-lm"
    assert request.model_configurations[0].is_visible is True
