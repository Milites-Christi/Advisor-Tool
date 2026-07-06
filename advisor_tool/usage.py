"""Helpers for reading the per-iteration usage breakdown on advisor-tool responses."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class UsageSummary:
    executor_input_tokens: int
    executor_output_tokens: int
    advisor_input_tokens: int
    advisor_output_tokens: int
    advisor_calls: int


def _as_dict(iteration: Any) -> Dict:
    # SDK objects and plain dicts both need to work here.
    if isinstance(iteration, dict):
        return iteration
    return iteration.model_dump() if hasattr(iteration, "model_dump") else vars(iteration)


def summarize_usage(usage: Any) -> UsageSummary:
    """Summarize executor vs. advisor token usage from `response.usage.iterations`.

    Executor iterations are billed at the executor model's rates; advisor
    iterations (`type == "advisor_message"`) are billed at the advisor
    model's rates. This walks the full breakdown rather than the top-level
    `usage.input_tokens`/`output_tokens`, which only reflect executor
    tokens.
    """
    iterations = getattr(usage, "iterations", None)
    if iterations is None and isinstance(usage, dict):
        iterations = usage.get("iterations", [])
    iterations = iterations or []

    executor_input = executor_output = advisor_input = advisor_output = 0
    advisor_calls = 0

    for raw in iterations:
        it = _as_dict(raw)
        if it.get("type") == "advisor_message":
            advisor_calls += 1
            advisor_input += it.get("input_tokens", 0) or 0
            advisor_output += it.get("output_tokens", 0) or 0
        else:
            executor_input += it.get("input_tokens", 0) or 0
            executor_output += it.get("output_tokens", 0) or 0

    return UsageSummary(
        executor_input_tokens=executor_input,
        executor_output_tokens=executor_output,
        advisor_input_tokens=advisor_input,
        advisor_output_tokens=advisor_output,
        advisor_calls=advisor_calls,
    )


def iter_advisor_results(content: List[Any]):
    """Yield `(server_tool_use_block, advisor_tool_result_block)` pairs from a turn's content."""
    pending = None
    for block in content:
        block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if block_type == "server_tool_use":
            name = getattr(block, "name", None) or (block.get("name") if isinstance(block, dict) else None)
            if name == "advisor":
                pending = block
        elif block_type == "advisor_tool_result" and pending is not None:
            yield pending, block
            pending = None
