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

## ⚠️ Two Hermes quirks you must work around

### 1. `hermes plugins install` clones to the wrong place for model providers

The installer always lands a plugin **top-level**:

```
~/.hermes/plugins/<name>/          ← where `hermes plugins install` puts things
```

But model-provider discovery only scans **two** locations (`providers/__init__.py`):

```
1. <hermes-repo>/plugins/model-providers/<name>/     ← bundled
2. $HERMES_HOME/plugins/model-providers/<name>/      ← user
```

A plugin that lands top-level is **explicitly skipped** by the flat scanner
(`Skipping '<name>' (model-provider, handled by providers/ discovery)`), and the provider
discovery never looks there. Net result: it silently does nothing.

→ **Fix: symlink into `model-providers/`.** Discovery uses `Path.is_dir()`, which follows
symlinks, so a symlink is indistinguishable from a real directory here.

### 2. Installing a SUBDIRECTORY loses `.git`, so `update` breaks

`_install_plugin_core()` clones to a temp dir, then does `shutil.move()` on the target:

```python
if subdir:
    tmp_target = _resolve_subdir_within(tmp_clone, subdir)   # only the subdir
else:
    tmp_target = tmp_clone                                   # the whole clone
shutil.move(str(tmp_target), str(target))
```

Install a subdir (`owner/repo/plugin`) and **only that subdir is moved** — `.git` stays behind
in the temp dir and is deleted. `hermes plugins update` then fails permanently:

```
Error: Plugin 'x' was not installed from git (no .git directory). Cannot update.
```

→ **Fix: install the WHOLE repo**, then point the symlinks at subdirectories *inside* the
clone. The clone keeps `.git`, so `update` works, and one update refreshes every plugin in the
repo at once.

## Install

```bash
# 1. Install the WHOLE repo (keeps .git → updates work)
hermes plugins install fabzter/hermes-model-providers --no-enable

# 2. Symlink each plugin into the directory discovery actually scans
ln -s ~/.hermes/plugins/hermes-model-providers/token-plan-personal \
      ~/.hermes/plugins/model-providers/token-plan-personal
ln -s ~/.hermes/plugins/hermes-model-providers/openai-codex \
      ~/.hermes/plugins/model-providers/openai-codex
```

Verify the symlinks resolve:

```bash
ls -la ~/.hermes/plugins/model-providers/
```

Then **restart Hermes** — plugin changes do not reload in a running process.

## Update

```bash
hermes plugins update hermes-model-providers
```

One command updates both providers: `git pull` on the clone, and the symlinks follow
automatically.

## Verify the whole path works

```bash
# must print a commit hash — if it says "not a git repository", you installed a subdir
git -C ~/.hermes/plugins/hermes-model-providers log --oneline -1

# must show the plugin version through the symlink
grep ^version ~/.hermes/plugins/model-providers/token-plan-personal/plugin.yaml
```

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
picker then fell back to the plugin's static `fallback_models` — a hand-maintained list — so
newly released models never appeared.

Concretely: `glm-5.3` was live on the endpoint while the picker showed `glm-5.2`.

The fix is one line — point the catalog probe at the OpenAI-compatible sibling endpoint:

```python
models_url="https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/models",
```

`fallback_models` is kept as a static safety net for when the catalog endpoint is unreachable.
It lists **text-generation models only** — image / audio / video IDs are deliberately kept out
of the chat picker.

> **`hermes model --refresh` / `/model --refresh` cannot fix this class of problem.** Those
> commands bust the *cache*, but the cache was never the issue — the fetch itself could not
> succeed, so there was nothing fresh to cache. Symptom to recognize: *"I refreshed and the
> list is still old."* Check whether the provider's catalog endpoint actually responds before
> blaming the cache.

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

Both quirks above look like **upstream gaps** worth reporting:

1. `hermes plugins install` does not honor a plugin's declared `kind: model-provider` when
   choosing a destination.
2. Subdirectory installs drop `.git`, making `hermes plugins update` impossible for any plugin
   that lives below a repo root.

If either is fixed, the corresponding workaround here becomes unnecessary.

## License

MIT
