"""Builder for the `advisor_20260301` tool definition."""

from typing import Literal, Optional

_VALID_TTLS = {"5m", "1h"}
_MIN_MAX_TOKENS = 1024


def build_advisor_tool(
    model: str,
    *,
    name: str = "advisor",
    max_uses: Optional[int] = None,
    max_tokens: Optional[int] = None,
    caching_ttl: Optional[Literal["5m", "1h"]] = None,
) -> dict:
    """Build a tool definition dict for the advisor tool.

    Args:
        model: Advisor model ID (e.g. "claude-opus-4-8").
        name: Tool name the executor sees. Must stay "advisor" unless you
            have a specific reason to rename it.
        max_uses: Per-request cap on advisor calls. Once exceeded, further
            calls return an `advisor_tool_result_error` with
            error_code "max_uses_exceeded".
        max_tokens: Caps the advisor's total output (thinking + text) per
            call. Minimum 1024. Unset means the advisor model's own output
            cap applies.
        caching_ttl: "5m" or "1h" to enable prompt caching of the advisor's
            own transcript across calls in a conversation. Only worth
            enabling when you expect 3+ advisor calls per conversation.

    Returns:
        A dict suitable for the `tools` array of a `beta.messages.create`
        call (with the advisor beta header set).
    """
    if max_tokens is not None and max_tokens < _MIN_MAX_TOKENS:
        raise ValueError(f"max_tokens must be >= {_MIN_MAX_TOKENS}, got {max_tokens}")
    if max_uses is not None and max_uses < 1:
        raise ValueError(f"max_uses must be >= 1, got {max_uses}")
    if caching_ttl is not None and caching_ttl not in _VALID_TTLS:
        raise ValueError(f"caching_ttl must be one of {_VALID_TTLS}, got {caching_ttl!r}")

    tool: dict = {
        "type": "advisor_20260301",
        "name": name,
        "model": model,
    }
    if max_uses is not None:
        tool["max_uses"] = max_uses
    if max_tokens is not None:
        tool["max_tokens"] = max_tokens
    if caching_ttl is not None:
        tool["caching"] = {"type": "ephemeral", "ttl": caching_ttl}
    return tool
