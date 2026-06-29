# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A learning project: a sequence of standalone `step-NN.py` scripts that progressively teach the Anthropic Python SDK (
`anthropic==0.112.0`). Each step is self-contained, runnable on its own, and builds on the concepts of the previous one.
There is no shared library, package, or test suite — the scripts *are* the deliverable.

The progression:

- `step-01.py` — SDK init smoke test (`anthropic.Anthropic()`).
- `step-02.py` — single message with a system prompt; inspecting `stop_reason` and `usage` token counts.
- `step-03.py` — multi-turn conversation by manually appending to a `messages` list.
- `step-04.py` — interactive REPL chat loop; lists available models; accumulates token usage.
- `step-05.py` — tool use (`get_weather`, `convert_temperature`) with a **synchronous** tool-call loop.
- `step-06.py` — same tools, **async** with concurrent tool execution via `asyncio.to_thread` + `asyncio.gather`.
- `step-06b.py` — refinement of 06: adds `logging`, bounded tool loop (`MAX_TURNS`), and SDK exception handling.

When asked to "add the next step," follow this pattern: a new top-numbered `step-NN.py` that introduces one new SDK
concept, kept runnable end-to-end with a `print(...)` or REPL at the bottom.

## Running

Managed with `uv` (see `uv.lock`, `pyproject.toml`); requires Python >= 3.14.

```bash
uv run step-05.py        # run any single step
```

The SDK reads `ANTHROPIC_API_KEY` from the environment. The key lives in `.env`, but **nothing in these scripts
loads `.env`** (there is no `python-dotenv` dependency) — it is injected by the IDE run config (`.idea/`) or must be
exported manually:

```bash
export $(grep -v '^#' .env | xargs) && uv run step-04.py
```

There are no build, lint, or test commands — the project has no test framework or linter configured.

## Conventions specific to this codebase

- **Model selection by commenting.** Each `messages.create` call lists candidate models as commented lines with exactly
  one active; switch models by moving the comment. Keep this idiom when editing.
- **Tool definitions use the typed param classes** — `ToolParam` + `InputSchemaTyped` from `anthropic.types`, not raw
  dicts. Tool *results* use `ToolResultBlockParam`.
- **The tool-use loop pattern** (step-05/06/06b): call the model → if no `tool_use` blocks, return the text → else
  execute each tool, append the assistant turn (`response.content`) and a user turn of `tool_result` blocks, repeat.
  Tool results are JSON-serialized (`json.dumps`) into the `content` field.
- **Async tool execution** wraps the blocking tool functions in `asyncio.to_thread` and awaits them with
  `asyncio.gather`; the `time.sleep(1)` calls in the tools exist only to demonstrate the concurrency, not as real
  latency.
- The `get_weather` / `convert_temperature` tools are **simulated** (hardcoded data), standing in for real API calls.

## Notes

- `.junie/` is JetBrains Junie assistant state (memory/plans), not application code.
- Per the project's tutorial nature and the global CLAUDE.md guidance: prefer minimal, surgical changes and avoid
  introducing abstractions or dependencies a learning script doesn't need.
