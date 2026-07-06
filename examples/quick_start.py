"""Minimal single-turn advisor tool call.

Requires ANTHROPIC_API_KEY in the environment.

    python examples/quick_start.py
"""

from advisor_tool import AdvisorToolClient, build_advisor_tool

client = AdvisorToolClient()

response = client.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=[build_advisor_tool(model="claude-opus-4-8")],
    messages=[
        {
            "role": "user",
            "content": "Build a concurrent worker pool in Go with graceful shutdown.",
        }
    ],
)

print(response)
