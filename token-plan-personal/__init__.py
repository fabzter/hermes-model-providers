"""Alibaba Token Plan (Personal Edition) provider profile.

Personal Edition uses a dedicated Anthropic-compatible endpoint with a separate
API key tier (sk-sp- prefix). Not interchangeable with Coding Plan or Pay-as-you-go.
"""

from providers import register_provider
from providers.base import ProviderProfile

token_plan_personal = ProviderProfile(
    name="token-plan-personal",
    aliases=("token-plan", "alibaba-token-plan"),
    display_name="Alibaba Token Plan (Personal)",
    description="Personal Token Plan live text models — qwen3.8, qwen3.7, qwen3.6, glm-5.3/5.2, deepseek-v4",
    signup_url="https://www.alibabacloud.com/help/en/model-studio/token-plan-personal-overview",
    env_vars=("DASHSCOPE_API_KEY",),
    base_url="https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic",
    # The Anthropic-compatible inference path exposes NO catalog — requesting
    # {base_url}/models returns HTTP 404, so the live model fetch always failed
    # and the picker silently fell back to the static fallback_models below
    # (which is how glm-5.3 stayed invisible while the endpoint served it).
    # Point the catalog probe at the OpenAI-compatible sibling endpoint, which
    # does expose /models.
    models_url="https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/models",
    api_mode="anthropic_messages",
    auth_type="api_key",
    supports_health_check=False,
    # Static fallback (text-generation models only; image/audio/video IDs are
    # deliberately kept out of the chat picker). Verified against the live
    # /compatible-mode/v1/models list on 2026-09-24.
    fallback_models=(
        "qwen3.8-max",
        "qwen3.8-flash",
        "qwen3.7-max",
        "qwen3.7-plus",
        "qwen3.6-flash",
        "glm-5.3",
        "glm-5.2",
        "deepseek-v4-pro",
        "deepseek-v4.1-flash",
        "deepseek-v4-flash-0731",
    ),
)

register_provider(token_plan_personal)
