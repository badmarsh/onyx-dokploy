from onyx.llm.constants import LlmProviderNames
from onyx.server.manage.llm.models import LLMProviderUpsertRequest
from onyx.server.manage.llm.models import ModelConfigurationUpsertRequest


def normalize_openai_compatible_api_base(api_base: str) -> str:
    cleaned_api_base = api_base.strip().rstrip("/")
    return (
        cleaned_api_base
        if cleaned_api_base.endswith("/v1")
        else f"{cleaned_api_base}/v1"
    )


def build_static_openai_compatible_provider_request(
    *,
    name: str,
    api_key: str,
    api_base: str,
    model_name: str,
    existing_id: int | None = None,
) -> LLMProviderUpsertRequest:
    return LLMProviderUpsertRequest(
        id=existing_id,
        name=name,
        provider=LlmProviderNames.OPENAI,
        api_key=api_key,
        api_base=normalize_openai_compatible_api_base(api_base),
        model_configurations=[
            ModelConfigurationUpsertRequest(
                name=model_name,
                is_visible=True,
            )
        ],
        api_key_changed=True,
        is_auto_mode=False,
    )
