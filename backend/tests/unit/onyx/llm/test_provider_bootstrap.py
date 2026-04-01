from onyx.llm.provider_bootstrap import build_uncensored_lm_provider_request


def test_build_uncensored_lm_provider_request() -> None:
    request = build_uncensored_lm_provider_request(
        name="Uncensored LM",
        api_key="secret",
        api_base="https://example.com/functions/v1/uncensoredlm-api",
        model_name="uncensored-lm",
        existing_id=12,
    )

    assert request.id == 12
    assert request.name == "Uncensored LM"
    assert request.provider == "uncensored_lm"
    assert request.api_key == "secret"
    assert request.api_base == "https://example.com/functions/v1/uncensoredlm-api"
    assert request.is_auto_mode is False
    assert request.api_key_changed is True
    assert len(request.model_configurations) == 1
    assert request.model_configurations[0].name == "uncensored-lm"
    assert request.model_configurations[0].is_visible is True
