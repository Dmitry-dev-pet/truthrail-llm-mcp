"""MCP 2 Streamable HTTP adapter: sealed until authenticated and explicitly enabled.

No owner-specific access token, OAuth grant, or gateway credential is embedded
here. A separate, reviewed OAuth identity flow is required before connecting
ChatGPT as an authenticated user. A static bearer can be used for isolated
operator acceptance, but must not be mistaken for end-user OAuth.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import uuid
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from llm_mcp.policy import (
    GATEWAY_URL, MODEL, PUBLISHER, PROVIDER, MAX_RESPONSE_BYTES,
    LocalReviewQuota, ReviewPolicyError, checked_public_python,
    make_payload, parse_upstream_reply,
)

SERVER_NAME = "Truthrail LLM Adapter"
REVIEW_ROUTE = "render-python-code-review"
REVIEW_ENABLED = os.getenv("ENABLE_REVIEW", "false").lower() == "true"
_AUTH_TOKEN = os.getenv("MCP_AUTH_BEARER", "")
_GATEWAY_KEY = os.getenv("GATEWAY_CLIENT_KEY", "")
_SECRET_PATTERN = re.compile(r"[A-Za-z0-9._/+=~:-]{32,512}\Z")
AUTH_VALID = bool(_SECRET_PATTERN.fullmatch(_AUTH_TOKEN))
GATEWAY_VALID = bool(_SECRET_PATTERN.fullmatch(_GATEWAY_KEY))
QUOTA = LocalReviewQuota()


# This application does not grant MCP clients model spending authority until
# all of: an explicit, protected client credential; a reviewed gateway client
# key; and an explicit enable switch have been provisioned.
def operational() -> bool:
    return bool(REVIEW_ENABLED and AUTH_VALID and GATEWAY_VALID)


mcp = MCPServer(SERVER_NAME)


@mcp.tool()
def get_adapter_status() -> dict[str, Any]:
    """Describe this authenticated connector's narrow capabilities; no secrets or inference."""
    return {
        "service": "truthrail-llm-mcp",
        "state": "ready_for_limited_review" if operational() else "sealed_no_model_access",
        "review_route": REVIEW_ROUTE,
        "publisher": PUBLISHER,
        "broker": PROVIDER,
        "model": MODEL,
        "scope": "public_python_correctness_review_only",
        "other_models_allowed": False,
        "direct_repository_access": False,
        "model_tools": False,
        "gateway_management_access": False,
    }


@mcp.tool()
def review_public_python(
    code: str,
    source_label: str,
    classification: str,
    share_with_opencode_go: bool,
) -> dict[str, Any]:
    """One explicitly approved PUBLIC Python correctness review; no private source or tools.

    Do not call without the repository owner's approval for THIS exact public
    snippet to be sent to OpenCode Go. This tool cannot read files or GitHub.
    """
    if not operational():
        return {"status": "blocked", "reason": "model_access_not_provisioned"}
    try:
        snippet = checked_public_python(
            code=code, source_label=source_label,
            classification=classification, consent=share_with_opencode_go,
        )
        QUOTA.begin()
    except ReviewPolicyError as exc:
        return {"status": "blocked", "reason": str(exc)}
    try:
        headers = {
            "Authorization": "Bearer " + _GATEWAY_KEY,
            "X-OpenCode-Session": str(uuid.uuid4()),
            "User-Agent": "Truthrail-Coding-Agent/1.0",
            "Content-Type": "application/json",
        }
        # No caller URL or proxy environment can change this destination.
        with httpx.Client(timeout=httpx.Timeout(35, connect=5), follow_redirects=False, trust_env=False) as client:
            response = client.post(GATEWAY_URL, json=make_payload(code=code, source=source_label), headers=headers)
        if response.status_code != 200 or len(response.content) > MAX_RESPONSE_BYTES:
            return {"status": "blocked", "reason": "upstream_transport_or_size_failure"}
        parsed = parse_upstream_reply(response.json(), protected_values=(_AUTH_TOKEN, _GATEWAY_KEY))
        return {
            "status": "executed_needs_owner_review",
            "route": REVIEW_ROUTE,
            "model": MODEL,
            "publisher": PUBLISHER,
            "broker": PROVIDER,
            "source": snippet["source"],
            "input_sha256": snippet["sha256"],
            **parsed,
        }
    except (ReviewPolicyError, httpx.HTTPError, ValueError, TypeError) as exc:
        if isinstance(exc, ReviewPolicyError):
            return {"status": "blocked", "reason": str(exc)}
        return {"status": "blocked", "reason": "upstream_response_or_connection_failure"}
    finally:
        QUOTA.finish()


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    # Deliberately no environment-variable values, tokens or account identity.
    return JSONResponse({"service": "truthrail-llm-mcp", "status": "ok", "inference": "disabled" if not operational() else "enabled"})


security = TransportSecuritySettings(
    allowed_hosts=[
        "truthrail-llm-mcp.onrender.com",
        "truthrail-llm-mcp.onrender.com:*",
        "localhost:*",
        "127.0.0.1:*",
    ],
    # Server-to-server clients don't send an Origin. Browser origins not enabled.
    allowed_origins=[],
)
_inner = mcp.streamable_http_app(
    stateless_http=True, json_response=True, transport_security=security,
    max_request_body_size=10000,
)


async def app(scope: dict, receive: Any, send: Any) -> None:
    """Enforce private bearer on every route except the fixed public health path."""
    if scope["type"] == "http" and scope.get("path") != "/health":
        raw = [v for k, v in scope.get("headers", []) if k.lower() == b"authorization"]
        good = len(raw) == 1 and AUTH_VALID and raw[0].startswith(b"Bearer ")
        if good:
            offered = raw[0][7:]
            good = 32 <= len(offered) <= 512 and hmac.compare_digest(
                offered, _AUTH_TOKEN.encode("ascii")
            )
        if not good:
            response = PlainTextResponse(
                "MCP authentication is required", status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="truthrail-llm-mcp"', "Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return
    await _inner(scope, receive, send)
