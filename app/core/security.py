"""Tier × block access control for the public block surface.

The audit found that a single API key reaches every registered block via
`/v1/execute`, `/chain`, and `/mcp`. Blocks like `code`, `sandbox`,
`formula_executor`, `secrets`, `database`, `web`, `webhook`,
`file_hasher`, `storage`, `email`, and `billing` are RCE / SSRF / FS
traversal / vault-read primitives. Combined with the public-tier API
key shipped in the SPA bundle, that's a server-compromise vector.

This module defines the set of blocks that require the `unlimited` tier
(master / dev keys only) and the helper `enforce_block_access` used by
the route handlers.

Override at runtime by setting `CEREBRUM_RESTRICTED_BLOCKS` to a
comma-separated list. To open a normally-restricted block to standard
tier, prefix with `-`:

    CEREBRUM_RESTRICTED_BLOCKS=-email,my_custom_dangerous_block
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Set

from fastapi import HTTPException

logger = logging.getLogger(__name__)


# Blocks that the audit identified as critical RCE / SSRF / vault / FS
# primitives. Standard-tier keys (including the SPA-shipped public key)
# get HTTP 403 when invoking any of these via /v1/execute, /chain, or
# /mcp. Unlimited tier (master, dev) bypasses the restriction.
_DEFAULT_RESTRICTED_BLOCKS: Set[str] = {
    # Code execution → arbitrary subprocess with full host environment.
    "code",
    "sandbox",
    "formula_executor",
    # Vault read.
    "secrets",
    # Raw SQL with no parameterisation guarantees.
    "database",
    # Outbound HTTP — no SSRF guard, response body returned to caller.
    "web",
    "webhook",
    # File-system primitives that lack the local_drive sandbox.
    "file_hasher",
    "storage",
    # Mail relay.
    "email",
    # State mutation (billing usage, plan upgrades).
    "billing",
}


def _parse_env_overrides() -> Set[str]:
    """Apply CEREBRUM_RESTRICTED_BLOCKS overrides on top of the default set.

    Each entry is a block name. Prefix with `-` to remove an existing entry.
    Whitespace is stripped. Empty entries are ignored.
    """
    raw = os.getenv("CEREBRUM_RESTRICTED_BLOCKS", "").strip()
    restricted: Set[str] = set(_DEFAULT_RESTRICTED_BLOCKS)
    if not raw:
        return restricted
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if token.startswith("-"):
            restricted.discard(token[1:])
        else:
            restricted.add(token)
    return restricted


# Resolve once at import time. Reload would require a process restart,
# which matches the operational model for changing security policy.
RESTRICTED_BLOCKS: Set[str] = _parse_env_overrides()
logger.info(
    "security: %d restricted block(s) — unlimited-tier only: %s",
    len(RESTRICTED_BLOCKS),
    ", ".join(sorted(RESTRICTED_BLOCKS)) or "(none)",
)


def is_restricted(block_name: str) -> bool:
    return block_name in RESTRICTED_BLOCKS


def enforce_block_access(block_name: str, auth: Dict[str, Any]) -> None:
    """Raise HTTPException(403) if `auth` lacks access to `block_name`.

    The check is permissive by default: only blocks in `RESTRICTED_BLOCKS`
    require `tier == "unlimited"`. Everything else is reachable by any
    valid API key.

    Call this AFTER `require_api_key` in the route handler — `auth` is
    the dict it returns.
    """
    if block_name not in RESTRICTED_BLOCKS:
        return
    tier = (auth or {}).get("tier")
    if tier == "unlimited":
        return
    user = (auth or {}).get("user", "?")
    logger.warning(
        "security: blocked %s (tier=%s) from invoking restricted block '%s'",
        user, tier, block_name,
    )
    raise HTTPException(
        status_code=403,
        detail=(
            f"Block '{block_name}' is restricted to unlimited-tier keys. "
            f"Your tier: {tier or 'unknown'}."
        ),
    )


# ── /mcp gate ─────────────────────────────────────────────────────────────
# /mcp exposes BLOCK_REGISTRY entries as MCP tools, including the
# restricted set. Without authentication on the SSE transport, anyone on
# the public internet has RCE. We require Bearer auth + tier=unlimited
# by default; override via CEREBRUM_MCP_REQUIRED_TIER (e.g. "standard"
# if you need to broaden the surface) or CEREBRUM_MCP_DISABLE_AUTH=1
# (for local stdio testing only — never in production).

_MCP_REQUIRED_TIER = os.getenv("CEREBRUM_MCP_REQUIRED_TIER", "unlimited").strip().lower()
_MCP_DISABLE_AUTH = os.getenv("CEREBRUM_MCP_DISABLE_AUTH", "").strip().lower() in (
    "1", "true", "yes",
)


def _send_status_only(status: int, message: str):
    """Build an ASGI send-callable closure that emits a JSON error response."""
    body = (
        '{"error":"' + message.replace('"', "\\\"") + '"}'
    ).encode("utf-8")

    async def _send(send):
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })

    return _send


def asgi_auth_required(inner_app, *, required_tier: str = _MCP_REQUIRED_TIER):
    """Wrap a Starlette/ASGI app to require Bearer auth + tier check.

    Used to gate /mcp. Skips checks when CEREBRUM_MCP_DISABLE_AUTH=1 so
    local stdio/SSE testing doesn't have to mint a key.
    """
    if _MCP_DISABLE_AUTH:
        logger.warning(
            "security: CEREBRUM_MCP_DISABLE_AUTH=1 — /mcp is unauthenticated. "
            "Do not enable in production."
        )
        return inner_app

    # Lazy import to avoid circular dep at module-load (security imports
    # before main.py finishes module init).
    from app.core.auth import auth as auth_manager

    async def _wrapped(scope, receive, send):
        if scope.get("type") not in ("http",):
            # Non-HTTP (websocket, lifespan, etc.) — pass through. SSE is
            # plain HTTP so it's covered by the "http" branch.
            await inner_app(scope, receive, send)
            return

        headers = {
            k.decode().lower(): v.decode()
            for k, v in scope.get("headers", [])
        }
        auth_header = headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            await _send_status_only(401, "Authorization: Bearer <key> required")(send)
            return
        key = auth_header[7:].strip()

        # Reach into the auth manager directly — validate_key wants
        # HTTPAuthorizationCredentials and raises HTTPException, neither
        # of which fits ASGI cleanly.
        auth_manager._maybe_reload()
        key_data = auth_manager._keys.get(key)
        if not key_data:
            await _send_status_only(401, "Invalid API key")(send)
            return

        tier = key_data.get("tier")
        if required_tier and tier != required_tier:
            await _send_status_only(
                403,
                f"/mcp requires tier '{required_tier}'. Your tier: {tier}.",
            )(send)
            return

        await inner_app(scope, receive, send)

    return _wrapped
