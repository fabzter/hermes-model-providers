# hermes-model-providers

Model-provider plugins for [Hermes Agent](https://github.com/NousResearch/hermes-agent) that
override or extend the bundled provider profiles.

| Plugin | What it does |
| --- | --- |
| **`token-plan-personal`** | Alibaba Cloud Model Studio **Token Plan (Personal Edition)** — Anthropic-compatible inference with a live model catalog |
| **`openai-codex`** | **OpenAI Codex (ChatGPT Plus)** — adds `fallback_models` so the `/model` picker lists the models a ChatGPT Plus subscription exposes |

Both are *user overrides*: they register a `ProviderProfile` of the same name as a bundled
profile, and user plugins win on name collision (last-writer-wins in `register_provider()`).

---

## ⚠️ Read this before installing

**`hermes plugins install` alone will NOT work for model providers.**

The installer always clones to a **top-level** path:

```
~/.hermes/plugins/<name>/          ← where `hermes plugins install` puts things
```

But model-provider discovery only scans **two** locations (`providers/__init__.py`):

```
1. <hermes-repo>/plugins/model-providers/<name>/     ← bundled
2. $HERMES_HOME/plugins/model-providers/<name>/      ← user
```

A plugin that lands top-level is **explicitly skipped** by the flat plugin scanner
(`Skipping '<name>' (model-provider, handled by providers/ discovery)`) — and then the
provider discovery never looks where it was installed. Net result: it silently does nothing.

## Install

```bash
# 1. Install from GitHub (lands top-level — expected)
hermes plugins install fabzter/hermes-model-providers/token-plan-personal
hermes plugins install fabzter/hermes-model-providers/openai-codex

# 2. Bridge the path mismatch with a symlink
#    (discovery uses Path.is_dir(), which follows symlinks — so this works)
ln -s ~/.hermes/plugins/token-plan-personal \
      ~/.hermes/plugins/model-providers/token-plan-personal
ln -s ~/.hermes/plugins/openai-codex \
      ~/.hermes/plugins/model-providers/openai-codex
```

Verify:

```bash
ls -la ~/.hermes/plugins/model-providers/
```

You should see the symlinks alongside any real directories. Restart Hermes (plugin changes do
not reload in a running process), then check the picker with `/model`.

## Update

```bash
hermes plugins update token-plan-personal
hermes plugins update openai-codex
```

The symlink follows the clone, so no extra step is needed after an update.

## Why the symlink instead of just copying

Copying works but loses the point: every upstream refresh means re-copying by hand, and a
Hermes upgrade that touches `~/.hermes/plugins/` can overwrite a hand-placed directory with no
trace. Cloning + symlinking keeps **GitHub as the single source of truth** while satisfying the
discovery path.

---

## `token-plan-personal`

Alibaba Cloud Model Studio — Token Plan (Personal Edition). Dedicated API key tier
(`sk-sp-` prefix); **not** interchangeable with Coding Plan or pay-as-you-go keys.

- **Inference:** `https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic`
  (`api_mode: anthropic_messages`)
- **Catalog:** `https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/models`

### The bug this plugin fixes

The Anthropic-compatible inference path **does not expose a model catalog** — requesting
`/apps/anthropic/v1/models` returns **HTTP 404**. Because `models_url` was unset, Hermes built
the probe URL as `{base_url}/models`, hit the 404, and the live fetch failed silently. The
picker then fell back to the plugin's static `fallback_models` — a hand-maintained list — and
newly released models never appeared.

Concretely: `glm-5.3` was live on the endpoint while the picker showed `glm-5.2`.

The fix is one line — point the catalog probe at the OpenAI-compatible sibling endpoint:

```python
models_url="https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/models",
```

`fallback_models` is kept as a static safety net for when the catalog endpoint is unreachable.
It lists **text-generation models only** — image / audio / video IDs are deliberately kept out
of the chat picker.

> `hermes model --refresh` / `/model --refresh` cannot fix this class of problem. Those commands
> bust the *cache*, but the cache was never the issue — the fetch itself could not succeed, so
> there was nothing fresh to cache.

### Known limitation

The live catalog returns **every** model the endpoint serves, including non-chat models
(`wan2.7-image`, `wan2.7-image-pro`, `qwen-audio-3.0-tts-plus`,
`qwen-audio-3.0-realtime-plus`). Those now show up in the chat picker alongside the text
models. Filtering them would require overriding `fetch_models()` in this profile — not done
yet, since it trades a live catalog for a hardcoded deny-list.

---

## `openai-codex`

OpenAI Codex via the Responses API (`codex_responses`), authenticated by ChatGPT Plus OAuth
(`auth_type: oauth_external`, no API key). The profile exists to supply `fallback_models` so
the picker can display the model list; without it the picker has nothing to show for an
OAuth-external provider.

---

## Contributing / upstream

The install-path mismatch described above looks like an **upstream gap**: `hermes plugins
install` does not honor a plugin's declared `kind: model-provider` when choosing a destination.
If that is fixed, the symlink step in the install instructions becomes unnecessary.

## License

MIT
