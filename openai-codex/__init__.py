"""OpenAI Codex (Responses API) provider profile — user override.

Adds fallback_models so the /model picker shows available models for
ChatGPT Plus subscriptions. Overrides the bundled plugin (last-writer-wins).
"""

from providers import register_provider
from providers.base import ProviderProfile

openai_codex = ProviderProfile(
    name="openai-codex",
    aliases=("codex", "openai_codex"),
    api_mode="codex_responses",
    env_vars=(),  # OAuth external — no API key
    base_url="https://chatgpt.com/backend-api/codex",
    auth_type="oauth_external",
    fallback_models=(
        # GPT-5.6 family (recommended for ChatGPT sign-in)
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        # Previous gen still available on Plus
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
    ),
)

register_provider(openai_codex)
