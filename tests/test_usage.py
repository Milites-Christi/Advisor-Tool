from types import SimpleNamespace

from advisor_tool.usage import iter_advisor_results, summarize_usage


def test_summarize_usage_separates_executor_and_advisor_tokens():
    usage = SimpleNamespace(
        iterations=[
            {"type": "message", "input_tokens": 412, "output_tokens": 89},
            {
                "type": "advisor_message",
                "model": "claude-opus-4-8",
                "input_tokens": 823,
                "output_tokens": 1612,
            },
            {"type": "message", "input_tokens": 1348, "output_tokens": 442},
        ]
    )

    summary = summarize_usage(usage)

    assert summary.executor_input_tokens == 412 + 1348
    assert summary.executor_output_tokens == 89 + 442
    assert summary.advisor_input_tokens == 823
    assert summary.advisor_output_tokens == 1612
    assert summary.advisor_calls == 1


def test_summarize_usage_handles_empty_iterations():
    summary = summarize_usage(SimpleNamespace(iterations=[]))
    assert summary.advisor_calls == 0
    assert summary.executor_input_tokens == 0


def test_iter_advisor_results_pairs_blocks():
    content = [
        SimpleNamespace(type="text", text="thinking..."),
        SimpleNamespace(type="server_tool_use", id="srvtoolu_1", name="advisor", input={}),
        SimpleNamespace(
            type="advisor_tool_result",
            tool_use_id="srvtoolu_1",
            content={"type": "advisor_result", "text": "advice"},
        ),
        SimpleNamespace(type="text", text="final answer"),
    ]

    pairs = list(iter_advisor_results(content))

    assert len(pairs) == 1
    call, result = pairs[0]
    assert call.id == "srvtoolu_1"
    assert result.content["text"] == "advice"


def test_iter_advisor_results_ignores_non_advisor_server_tools():
    content = [
        SimpleNamespace(type="server_tool_use", id="srvtoolu_2", name="web_search", input={}),
        SimpleNamespace(
            type="advisor_tool_result",
            tool_use_id="srvtoolu_2",
            content={"type": "advisor_result", "text": "n/a"},
        ),
    ]
    assert list(iter_advisor_results(content)) == []
