from onyx.llm.constants import LlmProviderNames
from onyx.server.manage.llm.models import LLMProviderUpsertRequest
from onyx.server.manage.llm.models import ModelConfigurationUpsertRequest


def build_uncensored_lm_provider_request(
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
        provider=LlmProviderNames.UNCENSORED_LM,
        api_key=api_key,
        api_base=api_base.strip().rstrip("/"),
        model_configurations=[
            ModelConfigurationUpsertRequest(
                name=model_name,
                is_visible=True,
            )
        ],
        api_key_changed=True,
        is_auto_mode=False,
    )
