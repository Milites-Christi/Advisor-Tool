import pytest

from advisor_tool.config import is_valid_pair, validate_pair


def test_valid_pair_sonnet_opus():
    assert is_valid_pair("claude-sonnet-4-6", "claude-opus-4-8")


def test_invalid_pair_opus_executor_sonnet_advisor():
    # Opus 4.8 executor cannot be advised by a weaker Sonnet model.
    assert not is_valid_pair("claude-opus-4-8", "claude-sonnet-4-6")


def test_fable_only_advises_itself():
    assert is_valid_pair("claude-fable-5", "claude-fable-5")
    assert not is_valid_pair("claude-fable-5", "claude-opus-4-8")


def test_validate_pair_raises_on_unknown_executor():
    with pytest.raises(ValueError, match="Unknown or unsupported executor"):
        validate_pair("not-a-real-model", "claude-opus-4-8")


def test_validate_pair_raises_on_invalid_pair():
    with pytest.raises(ValueError, match="not a valid advisor"):
        validate_pair("claude-opus-4-8", "claude-sonnet-4-6")


def test_validate_pair_passes_silently_on_valid_pair():
    validate_pair("claude-sonnet-4-6", "claude-opus-4-8")
