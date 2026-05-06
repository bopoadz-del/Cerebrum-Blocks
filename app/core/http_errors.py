"""Shared HTTP error classification for router → block error translation.

Routers consume blocks. Blocks return either {"status":"success", ...} or
{"status":"error", "error":"..."} envelopes. The router has to translate the
error string into a meaningful HTTP status code so callers can react sensibly:

    503  = service unavailable — config missing, network/DNS failure,
           dependent backend down. The platform is fine but an optional
           integration isn't reachable. Caller should surface "service is
           degraded" instead of treating it as a bad request.
    422  = unprocessable entity — genuine input/processing problem the caller
           can fix (wrong field name, malformed file, bad value).

Used by capture.py originally; lifted here so agent_swarm, workflow, knowledge,
notification, upload, and chain routers can apply the same classification
instead of returning naked 422s for everything.
"""

from __future__ import annotations


_CONFIG_MARKERS = (
    "not configured",
    "api key required",
    "no api key",
    "credentials missing",
    "credit balance",
    "credit balance is too low",
    "insufficient balance",
    "quota exceeded",
    "rate limit",
    "ocr_unavailable",
    # Provider-side payment / billing failures — caller can't fix by retrying
    "402",
    "payment required",
    "billing",
    "insufficient_quota",
    "out of credits",
)

_NETWORK_MARKERS = (
    "connection",
    "name or service not known",
    "all connection attempts failed",
    "timed out",
    "unreachable",
    "ssl",
    "dns",
)


def classify_block_error(error_text: str) -> int:
    """Return an HTTP status code for a block error message.

    503 for config/network/credit failures (the platform is healthy, an
    optional integration isn't), 422 for genuine input/processing problems.
    """
    if not error_text:
        return 422
    lowered = error_text.lower()
    if any(m in lowered for m in _CONFIG_MARKERS):
        return 503
    if any(m in lowered for m in _NETWORK_MARKERS):
        return 503
    return 422
