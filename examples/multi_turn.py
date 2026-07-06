"""Multi-turn conversation using the advisor tool.

Shows carrying `advisor_tool_result` blocks forward across turns, which is
required — the API returns a 400 if a later turn drops the advisor tool
while advisor_tool_result blocks remain in history.

    python examples/multi_turn.py
"""

from advisor_tool import AdvisorToolClient, build_advisor_tool

client = AdvisorToolClient()
tools = [build_advisor_tool(model="claude-opus-4-8")]

messages = [
    {
        "role": "user",
        "content": "Build a concurrent worker pool in Go with graceful shutdown.",
    }
]

response = client.create(model="claude-sonnet-4-6", max_tokens=4096, tools=tools, messages=messages)
messages.append({"role": "assistant", "content": response.content})

messages.append({"role": "user", "content": "Now add a max-in-flight limit of 10."})
response = client.create(model="claude-sonnet-4-6", max_tokens=4096, tools=tools, messages=messages)
messages.append({"role": "assistant", "content": response.content})

print(response)
