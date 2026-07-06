"""Diagnose whether your ANTHROPIC_API_KEY / org has access to the advisor tool beta.

Makes exactly one minimal, low-token live API call, forcing an advisor
consult (via `tool_choice`) so a successful response proves the whole
round trip works, not just that the beta header was accepted. Prints a
clear diagnosis instead of a raw traceback.

Usage:

    export ANTHROPIC_API_KEY=sk-ant-...
    python check_access.py
    python check_access.py --executor claude-haiku-4-5-20251001 --advisor claude-sonnet-4-6
"""

import argparse
import os
import sys

import anthropic

from advisor_tool import AdvisorToolClient, build_advisor_tool, validate_pair


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--executor", default="claude-sonnet-4-6", help="Executor model ID to test.")
    parser.add_argument("--advisor", default="claude-opus-4-8", help="Advisor model ID to test.")
    return parser.parse_args()


def diagnose_status_error(e: anthropic.APIStatusError) -> str:
    status = e.status_code
    body = getattr(e, "body", None)
    message = ""
    if isinstance(body, dict):
        message = str(body.get("error", {}).get("message", "")) or str(body)
    else:
        message = str(e)

    lower = message.lower()

    if status == 400 and ("beta" in lower or "advisor" in lower):
        return (
            "NO ACCESS: the API rejected the request because of the advisor tool or its "
            f"beta header. Raw message: {message!r}\n"
            "This usually means your organization does not yet have the advisor_20260301 "
            "beta enabled. Check Console (console.anthropic.com) for beta/feature access, "
            "or contact Anthropic support/sales to request it."
        )
    if status == 400:
        return f"BAD REQUEST (not access-related): {message!r}\nCheck the model IDs and parameters."
    if status == 401:
        return f"AUTH FAILED: {message!r}\nYour ANTHROPIC_API_KEY looks invalid or missing."
    if status == 403:
        return (
            f"PERMISSION DENIED: {message!r}\n"
            "Your key is valid but lacks entitlement for this feature (or model). "
            "This is the access issue itself — contact Anthropic support/sales."
        )
    if status == 404:
        return f"NOT FOUND: {message!r}\nCheck the executor/advisor model IDs are correct and available to you."
    if status == 429:
        return f"RATE LIMITED: {message!r}\nAccess is likely fine — retry in a bit."
    return f"UNEXPECTED API ERROR (status {status}): {message!r}"


def main() -> None:
    args = parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        validate_pair(args.executor, args.advisor)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    client = AdvisorToolClient()
    tools = [build_advisor_tool(model=args.advisor, max_tokens=1024)]

    print(f"Testing executor={args.executor} advisor={args.advisor} ...")

    try:
        response = client.create(
            model=args.executor,
            max_tokens=512,
            tools=tools,
            tool_choice={"type": "tool", "name": "advisor"},
            messages=[{"role": "user", "content": "Say hello in one short sentence."}],
        )
    except anthropic.APIStatusError as e:
        print(diagnose_status_error(e))
        sys.exit(1)
    except anthropic.APIConnectionError as e:
        print(f"NETWORK ERROR: could not reach the API: {e}")
        sys.exit(1)

    advisor_result = None
    for block in response.content:
        if getattr(block, "type", None) == "advisor_tool_result":
            advisor_result = block.content
            break

    if advisor_result is None:
        print("UNEXPECTED: request succeeded but no advisor_tool_result block was returned.")
        print("Raw response content:")
        print(response.content)
        sys.exit(1)

    result_type = getattr(advisor_result, "type", None)
    if result_type == "advisor_tool_result_error":
        error_code = getattr(advisor_result, "error_code", "unknown")
        print(
            f"ACCESS OK, but the advisor call itself failed with error_code={error_code!r}.\n"
            "This is a transient/capacity issue on the advisor sub-inference, not a lack "
            "of access — the beta header and tool were accepted. Try again shortly."
        )
        sys.exit(0)

    print("ACCESS CONFIRMED: your key/org can use the advisor_20260301 beta.")
    print(f"Result type: {result_type}")
    if result_type == "advisor_result":
        print(f"Advisor said: {advisor_result.text[:200]}")
    elif result_type == "advisor_redacted_result":
        print("Advisor returned encrypted_content (expected for this advisor model).")


if __name__ == "__main__":
    main()
