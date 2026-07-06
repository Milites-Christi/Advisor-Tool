"""Agent loop with a Haiku executor, a custom tool, and the mid-conversation nudge.

Demonstrates the full pattern: an executor with its own tools, the advisor
tool, the turn-2 nudge for under-calling executors, and a usage summary at
the end that separates executor tokens from advisor tokens.

    python examples/agent_loop_with_nudge.py
"""

from advisor_tool import AdvisorToolClient, build_advisor_tool, summarize_usage

CODING_SYSTEM_PROMPT = """\
You have access to an `advisor` tool backed by a stronger reviewer model. It \
takes NO parameters — when you call advisor(), your entire conversation \
history is automatically forwarded.

Call advisor BEFORE substantive work — before writing, before committing to \
an interpretation, before building on an assumption. Also call it when you \
believe the task is complete (after making your deliverable durable), when \
stuck, or when considering a change of approach.
"""


def run_your_tools(content) -> list:
    """Stub tool dispatcher: replace with real dispatch to your own tools."""
    results = []
    for block in content:
        if getattr(block, "type", None) == "tool_use":
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"[stub] pretended to run {block.name}({block.input})",
                }
            )
    return results


client = AdvisorToolClient()

tools = [
    build_advisor_tool(model="claude-opus-4-8", max_tokens=2048),
    {
        "name": "run_bash",
        "description": "Run a bash command and return its output.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]

result = client.run_agent_loop(
    task="Build a concurrent worker pool in Go with graceful shutdown.",
    executor_model="claude-haiku-4-5-20251001",
    tools=tools,
    tool_dispatch=run_your_tools,
    system=CODING_SYSTEM_PROMPT,
    nudge_turn=2,
)

last_assistant = next(m for m in reversed(result.messages) if m["role"] == "assistant")
print("Final assistant turn:")
print(last_assistant["content"])

print("\nUsage per executor turn:")
for i, response in enumerate(result.responses, start=1):
    summary = summarize_usage(response.usage)
    print(
        f"  turn {i}: executor in={summary.executor_input_tokens} "
        f"out={summary.executor_output_tokens} | "
        f"advisor calls={summary.advisor_calls} "
        f"in={summary.advisor_input_tokens} out={summary.advisor_output_tokens}"
    )
