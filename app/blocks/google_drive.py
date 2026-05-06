"""Google Drive Block - real OAuth 2.0 + Drive API using refresh tokens"""

import base64
import json
import os
from typing import Any, Dict

import httpx

from app.core.universal_base import UniversalBlock

_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
_OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_DRIVE_API = "https://www.googleapis.com/drive/v3"


def _auth_url() -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return ""
    redirect = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
    scope = " ".join(_SCOPES)
    return (
        f"{_OAUTH_AUTH_URL}?client_id={client_id}"
        f"&redirect_uri={redirect}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )


async def _get_access_token() -> str:
    """Refresh access token using GOOGLE_REFRESH_TOKEN or fall back to GOOGLE_ACCESS_TOKEN."""
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if refresh_token and client_id and client_secret:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                _OAUTH_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["access_token"]
            raise RuntimeError(f"Token refresh failed ({resp.status_code}): {resp.text[:500]}")

    access_token = os.getenv("GOOGLE_ACCESS_TOKEN", "")
    if access_token:
        return access_token

    raise RuntimeError(
        "No Google credentials configured. Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET + GOOGLE_REFRESH_TOKEN, "
        "or set GOOGLE_ACCESS_TOKEN directly."
    )


class GoogleDriveBlock(UniversalBlock):
    """Google Drive: list, read, download files via OAuth 2.0"""

    name = "google_drive"
    version = "2.0"
    description = "Google Drive file operations — set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET + GOOGLE_REFRESH_TOKEN or GOOGLE_ACCESS_TOKEN"
    layer = 4
    tags = ["integration", "storage", "cloud", "google"]
    requires = []

    ui_schema = {
        "input": {
            "type": "text",
            "accept": ["*/*"],
            "placeholder": "File ID, folder name, or search query...",
            "multiline": False,
        },
        "output": {
            "type": "list",
            "fields": [{"name": "files", "type": "array", "label": "Files"}],
        },
        "quick_actions": [
            {"icon": "☁️", "label": "Browse Drive", "prompt": "List files from Google Drive"},
            {"icon": "🔑", "label": "Auth", "prompt": "Authenticate with Google Drive"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        operation = params.get("operation", "list")

        query = ""
        if isinstance(input_data, str):
            query = input_data
        elif isinstance(input_data, dict):
            query = input_data.get("query") or input_data.get("text") or ""
            operation = input_data.get("operation", operation)

        # ── Auth status / URL ─────────────────────────────────────────────────
        if operation in ("auth", "status"):
            has_refresh = bool(os.getenv("GOOGLE_REFRESH_TOKEN"))
            has_access = bool(os.getenv("GOOGLE_ACCESS_TOKEN"))
            has_creds = bool(os.getenv("GOOGLE_CLIENT_ID"))
            url = _auth_url()
            return {
                "status": "success",
                "operation": "auth",
                "authenticated": has_access or has_refresh,
                "credentials_configured": has_creds or has_access,
                "auth_url": url or None,
                "instructions": (
                    "Visit auth_url in a browser, approve, then capture the code and exchange it for a refresh token. "
                    "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in environment variables."
                    if url and not (has_access or has_refresh) else
                    "Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET + GOOGLE_REFRESH_TOKEN in env vars to enable OAuth."
                    if not (has_creds or has_access) else
                    "Credentials are set. Use operation=list to browse files."
                ),
            }

        # ── List files ────────────────────────────────────────────────────────
        if operation == "list":
            try:
                access_token = await _get_access_token()
            except RuntimeError as e:
                return {
                    "status": "success",
                    "mode": "unconfigured",
                    "error": str(e),
                    "auth_url": _auth_url() or None,
                    "instructions": "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN environment variables to enable Google Drive access.",
                    "files": [],
                }
            try:
                # Drive Query Language: single quotes terminate the literal,
                # so an unsanitised `query` lets the caller break out into
                # arbitrary clauses (e.g. "' or trashed=false or '"). Drive
                # has no escaping mechanism for q values; the safe move is
                # to reject any embedded single quote.
                if query and "'" in query:
                    return {
                        "status": "error",
                        "error": "Search query may not contain single quotes",
                    }
                q = f"name contains '{query}'" if query else "trashed=false"
                async with httpx.AsyncClient(timeout=20) as client:
                    resp = await client.get(
                        f"{_DRIVE_API}/files",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={
                            "q": q,
                            "pageSize": params.get("limit", 20),
                            "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink)",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                files = [
                    {
                        "id": f.get("id"),
                        "name": f.get("name"),
                        "type": f.get("mimeType", "").split("/")[-1],
                        "size_bytes": int(f.get("size", 0)),
                        "modified": f.get("modifiedTime", "")[:10],
                        "url": f.get("webViewLink", ""),
                    }
                    for f in data.get("files", [])
                ]
                return {"status": "success", "operation": "list", "files": files, "total": len(files)}
            except Exception as e:
                return {"status": "error", "error": str(e), "operation": "list"}

        # ── Download / read file ──────────────────────────────────────────────
        if operation == "download":
            file_id = query or params.get("file_id", "")
            if not file_id:
                return {"status": "error", "error": "file_id required for download"}
            try:
                access_token = await _get_access_token()
            except RuntimeError as e:
                return {"status": "error", "error": str(e)}
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(
                        f"{_DRIVE_API}/files/{file_id}",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"alt": "media"},
                    )
                    resp.raise_for_status()
                    content = resp.content
                return {
                    "status": "success",
                    "operation": "download",
                    "file_id": file_id,
                    "size_bytes": len(content),
                    "content_base64": base64.b64encode(content).decode(),
                }
            except Exception as e:
                return {"status": "error", "error": str(e), "operation": "download"}

        return {"status": "error", "error": f"Unknown operation: {operation}. Use: auth, list, download"}
