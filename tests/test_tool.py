import pytest

from advisor_tool.tool import build_advisor_tool


def test_minimal_tool_definition():
    tool = build_advisor_tool(model="claude-opus-4-8")
    assert tool == {
        "type": "advisor_20260301",
        "name": "advisor",
        "model": "claude-opus-4-8",
    }


def test_full_tool_definition():
    tool = build_advisor_tool(
        model="claude-opus-4-8",
        max_uses=5,
        max_tokens=2048,
        caching_ttl="5m",
    )
    assert tool["max_uses"] == 5
    assert tool["max_tokens"] == 2048
    assert tool["caching"] == {"type": "ephemeral", "ttl": "5m"}


def test_max_tokens_below_minimum_rejected():
    with pytest.raises(ValueError, match="max_tokens must be >= 1024"):
        build_advisor_tool(model="claude-opus-4-8", max_tokens=512)


def test_max_uses_below_one_rejected():
    with pytest.raises(ValueError, match="max_uses must be >= 1"):
        build_advisor_tool(model="claude-opus-4-8", max_uses=0)


def test_invalid_caching_ttl_rejected():
    with pytest.raises(ValueError, match="caching_ttl must be one of"):
        build_advisor_tool(model="claude-opus-4-8", caching_ttl="30m")
