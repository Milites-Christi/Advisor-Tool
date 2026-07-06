"""Model compatibility rules for the advisor tool.

The executor model (top-level `model`) and the advisor model (the tool
definition's `model`) must form a valid pair: the advisor must be at least
as capable as the executor. This table mirrors the compatibility matrix
documented for the `advisor_20260301` tool.
"""

ADVISOR_BETA_HEADER = "advisor-tool-2026-03-01"

# Advisor models that return `advisor_redacted_result` (encrypted_content)
# instead of plaintext `advisor_result`.
REDACTED_RESULT_MODELS = {
    "claude-fable-5",
    "claude-mythos-5",
}

_FABLE = "claude-fable-5"
_MYTHOS = "claude-mythos-5"
_OPUS_48 = "claude-opus-4-8"
_OPUS_47 = "claude-opus-4-7"
_OPUS_46 = "claude-opus-4-6"
_SONNET_46 = "claude-sonnet-4-6"

MODEL_COMPATIBILITY = {
    "claude-haiku-4-5-20251001": {_FABLE, _MYTHOS, _OPUS_48, _OPUS_47, _OPUS_46, _SONNET_46},
    "claude-sonnet-4-6": {_FABLE, _MYTHOS, _OPUS_48, _OPUS_47, _OPUS_46, _SONNET_46},
    "claude-sonnet-5": {_FABLE, _MYTHOS, _OPUS_48, _OPUS_47},
    "claude-opus-4-6": {_FABLE, _MYTHOS, _OPUS_48, _OPUS_47, _OPUS_46},
    "claude-opus-4-7": {_FABLE, _MYTHOS, _OPUS_48, _OPUS_47},
    "claude-opus-4-8": {_FABLE, _MYTHOS, _OPUS_48, _OPUS_47},
    _FABLE: {_FABLE},
    _MYTHOS: {_MYTHOS},
}


def is_valid_pair(executor_model: str, advisor_model: str) -> bool:
    """Return True if `advisor_model` is a valid advisor for `executor_model`."""
    return advisor_model in MODEL_COMPATIBILITY.get(executor_model, set())


def validate_pair(executor_model: str, advisor_model: str) -> None:
    """Raise ValueError if the executor/advisor pair is not supported.

    This is a client-side pre-check to fail fast with a clear message;
    the API itself is the source of truth and returns a 400 for invalid
    pairs regardless.
    """
    if executor_model not in MODEL_COMPATIBILITY:
        raise ValueError(
            f"Unknown or unsupported executor model: {executor_model!r}. "
            f"Supported executors: {sorted(MODEL_COMPATIBILITY)}"
        )
    if not is_valid_pair(executor_model, advisor_model):
        allowed = sorted(MODEL_COMPATIBILITY[executor_model])
        raise ValueError(
            f"{advisor_model!r} is not a valid advisor for executor "
            f"{executor_model!r}. Allowed advisors: {allowed}"
        )
