"""Thin wrapper around the Anthropic SDK for the advisor tool pattern."""

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List, Optional

import anthropic

from .config import ADVISOR_BETA_HEADER, validate_pair

DEFAULT_NUDGE_TEXT = (
    "You have not consulted the advisor yet. If the task has a non-obvious "
    "design decision or a failure mode you haven't ruled out, call advisor "
    "now before committing to an approach."
)


def _advisor_model_from_tool(tools: Iterable[dict]) -> Optional[str]:
    for tool in tools:
        if tool.get("type") == "advisor_20260301":
            return tool.get("model")
    return None


def _response_called_advisor(content) -> bool:
    return any(
        getattr(block, "type", None) == "server_tool_use"
        and getattr(block, "name", None) == "advisor"
        for block in content
    )


@dataclass
class AgentLoopResult:
    messages: List[dict]
    # One entry per executor turn (a "message" or "pause_turn" response),
    # in order. Use `advisor_tool.summarize_usage` on each to separate
    # executor tokens from advisor tokens.
    responses: List[Any] = field(default_factory=list)


class AdvisorToolClient:
    """Wraps `anthropic.Anthropic` to make advisor-tool calls less boilerplate.

    This does not reimplement the API; it just sets the beta header, does a
    client-side model-pair sanity check, and provides a small agent-loop
    helper for the nudge/tool-dispatch pattern documented for the advisor
    tool.
    """

    def __init__(self, client: Optional[anthropic.Anthropic] = None):
        self.client = client or anthropic.Anthropic()

    def create(self, *, model: str, tools: List[dict], messages: List[dict], **kwargs):
        """Call `beta.messages.create` with the advisor beta header set.

        Validates the executor/advisor model pair client-side when an
        advisor tool is present in `tools`.
        """
        advisor_model = _advisor_model_from_tool(tools)
        if advisor_model:
            validate_pair(model, advisor_model)

        betas = list(kwargs.pop("betas", []) or [])
        if ADVISOR_BETA_HEADER not in betas:
            betas.append(ADVISOR_BETA_HEADER)

        return self.client.beta.messages.create(
            model=model,
            tools=tools,
            messages=messages,
            betas=betas,
            **kwargs,
        )

    def run_agent_loop(
        self,
        *,
        task: str,
        executor_model: str,
        tools: List[dict],
        tool_dispatch: Optional[Callable[[list], List[dict]]] = None,
        max_turns: int = 10,
        max_tokens: int = 4096,
        nudge_turn: Optional[int] = 2,
        nudge_text: str = DEFAULT_NUDGE_TEXT,
        system: Optional[str] = None,
    ) -> AgentLoopResult:
        """Run a turn loop that calls your tools and applies the mid-conversation nudge.

        `tools` must include an advisor tool definition (see `build_advisor_tool`)
        plus any of your own client-side tools. `tool_dispatch` receives the
        content blocks of an assistant turn and must return one `tool_result`
        block per `tool_use` block it contains; it is not called for the
        advisor's `server_tool_use` block, which the API resolves itself.

        Set `nudge_turn=None` to disable the nudge (recommended for Opus
        executors and for system prompts that already ask the model to call
        the advisor sparingly).

        Returns an `AgentLoopResult` with the full `messages` list (so the
        caller can inspect or continue the conversation) and the raw
        responses from each executor turn (for usage/cost accounting).
        """
        messages: List[dict] = [{"role": "user", "content": task}]
        responses: List[Any] = []
        advisor_called = False

        for turn in range(1, max_turns + 1):
            kwargs = {"max_tokens": max_tokens}
            if system is not None:
                kwargs["system"] = system

            response = self.create(
                model=executor_model,
                tools=tools,
                messages=messages,
                **kwargs,
            )
            responses.append(response)
            messages.append({"role": "assistant", "content": response.content})
            advisor_called = advisor_called or _response_called_advisor(response.content)

            if response.stop_reason == "end_turn":
                break
            if response.stop_reason == "pause_turn":
                # A server tool (the advisor) is still pending; resending
                # the transcript as-is lets the API finish it.
                continue

            results: List[dict] = []
            if tool_dispatch is not None:
                results = tool_dispatch(response.content)
            if results:
                messages.append({"role": "user", "content": results})

            if nudge_turn is not None and turn == nudge_turn - 1 and not advisor_called:
                messages.append({"role": "user", "content": nudge_text})

        return AgentLoopResult(messages=messages, responses=responses)
