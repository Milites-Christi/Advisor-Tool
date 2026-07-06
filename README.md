# Advisor Tool

A Python starter kit for the Anthropic **advisor tool** (`advisor_20260301`, beta): pair a
faster, cheaper **executor model** with a higher-intelligence **advisor model** that gives
strategic guidance mid-generation. This fits long-horizon agentic workloads — coding
agents, computer use, multi-step research — where most turns are mechanical but a good
plan up front matters a lot.

> The advisor tool is a beta feature. Requests need the `advisor-tool-2026-03-01` beta
> header, which this project sets automatically.

## Install

```bash
pip install -r requirements.txt
# or: pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...   # see .env.example
```

## Quick start

```python
from advisor_tool import AdvisorToolClient, build_advisor_tool

client = AdvisorToolClient()

response = client.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=[build_advisor_tool(model="claude-opus-4-8")],
    messages=[{"role": "user", "content": "Build a concurrent worker pool in Go with graceful shutdown."}],
)
print(response)
```

Run the bundled examples:

```bash
python examples/quick_start.py            # single-turn call
python examples/multi_turn.py             # carrying advisor_tool_result across turns
python examples/agent_loop_with_nudge.py  # full agent loop: custom tools + nudge + usage accounting
```

## Interactive chat

`chat.py` is a terminal chat loop you leave running: type messages, the executor model
answers, and it consults the advisor model mid-turn when the situation calls for it.

```bash
python chat.py
# or, e.g. a cheap executor stepped up by a strong advisor:
python chat.py --executor claude-haiku-4-5-20251001 --advisor claude-opus-4-8 --verbose
```

In-chat commands: `/reset` clears history, `/usage` prints cumulative executor vs. advisor
token counts, `/exit` quits (or Ctrl-D / Ctrl-C). `--verbose` prints the advisor's actual
text and per-turn usage as it happens; without it you just see `[consulting advisor...]` /
`[advisor replied]` markers. See `python chat.py --help` for all flags (`--max-uses`,
`--advisor-max-tokens`, `--caching-ttl`, `--system`).

## What's in this package

- `advisor_tool/config.py` — the executor/advisor model compatibility matrix
  (`validate_pair`, `is_valid_pair`) and the beta header constant. The advisor must be at
  least as capable as the executor; this checks pairs client-side before hitting the API.
- `advisor_tool/tool.py` — `build_advisor_tool(...)` constructs a valid tool definition
  (`max_uses`, `max_tokens` floor of 1024, `caching` ttl of `"5m"`/`"1h"`) and rejects
  invalid values up front.
- `advisor_tool/client.py` — `AdvisorToolClient`:
  - `.create(...)` — wraps `client.beta.messages.create`, injecting the beta header and
    validating the model pair when an advisor tool is present.
  - `.run_agent_loop(...)` — a turn loop that dispatches your own tools, resumes
    `pause_turn` responses (a pending advisor call), and applies the documented
    turn-2 nudge for executors that under-call the advisor. Returns an
    `AgentLoopResult(messages, responses)`.
- `advisor_tool/usage.py` — `summarize_usage(response.usage)` separates executor tokens
  from advisor tokens using the `usage.iterations` breakdown (they're billed at different
  model rates and are not combined in the top-level `usage` fields). `iter_advisor_results`
  pairs up `server_tool_use`/`advisor_tool_result` blocks in a turn's content.

## Model compatibility

The advisor must be Claude Sonnet 4.6 or a more capable model, and at least as capable as
the executor:

| Executor | Valid advisors |
| --- | --- |
| Haiku 4.5 | Fable 5, Mythos 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6 |
| Sonnet 4.6 | Fable 5, Mythos 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6 |
| Sonnet 5 | Fable 5, Mythos 5, Opus 4.8, Opus 4.7 |
| Opus 4.6 | Fable 5, Mythos 5, Opus 4.8, Opus 4.7, Opus 4.6 |
| Opus 4.7 | Fable 5, Mythos 5, Opus 4.8, Opus 4.7 |
| Opus 4.8 | Fable 5, Mythos 5, Opus 4.8, Opus 4.7 |
| Fable 5 | Fable 5 |
| Mythos 5 | Mythos 5 |

`AdvisorToolClient.create` validates this pair client-side and raises `ValueError` before
making a request; the API enforces it server-side regardless with a `400`.

## Notes on cost and multi-turn use

- Advisor calls are billed separately at the advisor model's rates (`usage.iterations`
  entries with `type: "advisor_message"`). Use `summarize_usage` rather than the top-level
  `usage.input_tokens`/`output_tokens`, which only reflect the executor.
- There's no built-in conversation-level cap on advisor calls — use `max_uses` on the tool
  definition for a per-request cap, and count calls client-side for a conversation-level
  budget. When you drop the advisor tool from a conversation, also strip any
  `advisor_tool_result` blocks from history, or the API returns a `400`.
- Enable advisor-side caching (`build_advisor_tool(..., caching_ttl="5m")`) only when you
  expect 3+ advisor calls in a conversation — the cache write costs more than a couple of
  reads save.
- Cap advisor output with `build_advisor_tool(..., max_tokens=2048)` for a hard ceiling on
  cost/latency, or add a line to your user message (e.g. "Advisor: keep guidance under 80
  words") for a softer nudge toward brevity.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Tests cover the pure logic (model-pair validation, tool-definition building, usage
parsing) and don't require an API key.
