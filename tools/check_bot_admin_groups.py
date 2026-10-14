#!/usr/bin/env python3
"""Read-only check: is this bot an admin in each known Telegram chat?

Telegram's Bot API does not provide a method to enumerate every group a bot has
joined. Supply candidate chat IDs/usernames through AIINDEKSI_AUDIT_CHAT_IDS.
The script calls only getMe and getChatMember; it never sends a message.

Keep AIINDEKSI_TOKEN in a secret manager or protected environment variable. Do
not pass it as a command-line argument, save it in this file, or paste it into
chat. The script intentionally suppresses response bodies and exception text.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

API_ROOT = "https://api.telegram.org"
MAX_CANDIDATES = 100
_ALLOWED_METHODS = {"getMe", "getChatMember"}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward a token-bearing API request to a redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def parse_chat_ids(raw: str) -> list[str]:
    """Parse numeric Telegram IDs or @usernames; preserve order, remove duplicates."""
    values = re.split(r"[,;\s]+", (raw or "").strip())
    if not values or values == [""]:
        raise ValueError("No candidate chats were supplied")
    parsed: list[str] = []
    for value in values:
        if not value:
            continue
        if not (re.fullmatch(r"-?\d{1,20}", value) or
                re.fullmatch(r"@[A-Za-z0-9_]{5,32}", value)):
            raise ValueError("A candidate chat identifier has an invalid format")
        if value not in parsed:
            parsed.append(value)
    if not parsed:
        raise ValueError("No candidate chats were supplied")
    if len(parsed) > MAX_CANDIDATES:
        raise ValueError("Too many candidate chats; maximum is 100")
    return parsed


def _api_call(token: str, method: str, params: dict[str, Any] | None = None,
              timeout: int = 15) -> tuple[Any | None, str | None]:
    """Call an allowlisted read-only Bot API method and return a sanitized status."""
    if method not in _ALLOWED_METHODS:
        return None, "method_not_allowed"
    if not token:
        return None, "token_missing"
    url = f"{API_ROOT}/bot{token}/{method}"
    body = json.dumps(params or {}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never print the URL, headers, response body, or exception text.
        if exc.code == 401:
            return None, "auth_error"
        if exc.code in (400, 403, 404):
            return None, "chat_inaccessible"
        return None, "http_error"
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, "network_error"
    except (ValueError, TypeError):
        return None, "invalid_api_response"
    except Exception:  # noqa: BLE001 - error text could include the token-bearing URL
        return None, "request_error"

    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return None, "api_error"
    return payload.get("result"), None


def _member_status(result: Any, bot_id: int) -> str:
    if not isinstance(result, dict):
        return "unknown"
    user = result.get("user")
    if not isinstance(user, dict) or user.get("id") != bot_id:
        return "unknown"
    status = result.get("status")
    if status in ("creator", "administrator"):
        return "admin"
    if status in ("member", "restricted"):
        return "not_admin"
    if status in ("left", "kicked"):
        return "not_member"
    return "unknown"


def check_candidates(token: str, candidates: list[str]) -> tuple[list[str], str | None]:
    """Check the bot account against known chats; do not return chat IDs or titles."""
    me, error = _api_call(token, "getMe")
    if error:
        return [], error
    if not isinstance(me, dict) or not isinstance(me.get("id"), int):
        return [], "invalid_bot_identity"
    bot_id = me["id"]

    results: list[str] = []
    for chat_id in candidates:
        member, error = _api_call(token, "getChatMember", {
            "chat_id": chat_id,
            "user_id": bot_id,
        })
        results.append(error or _member_status(member, bot_id))
        if error == "auth_error":
            break
    return results, None


def main() -> int:
    token = os.environ.get("AIINDEKSI_TOKEN", "").strip()
    raw_candidates = os.environ.get("AIINDEKSI_AUDIT_CHAT_IDS", "")
    if not token:
        print("AIINDEKSI_TOKEN is not configured in the secure environment.")
        return 2
    try:
        candidates = parse_chat_ids(raw_candidates)
    except ValueError:
        print("Set AIINDEKSI_AUDIT_CHAT_IDS to known candidate chat IDs/usernames.")
        return 2

    statuses, error = check_candidates(token, candidates)
    if error:
        print(f"Bot admin check could not start: {error}.")
        return 1
    for index, status in enumerate(statuses, start=1):
        print(f"candidate {index}: {status}")
    print("Read-only check complete; no Telegram messages were sent.")
    print("Candidate order matches AIINDEKSI_AUDIT_CHAT_IDS; chat IDs/titles are not printed.")
    return 0 if statuses and all(s not in ("auth_error", "network_error", "http_error",
                                           "chat_inaccessible", "request_error", "api_error", "unknown")
                                  for s in statuses) else 1


if __name__ == "__main__":
    sys.exit(main())
