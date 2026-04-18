"""
Claude Code Bot — Telegram interface for Claude claude-sonnet-4-6
Full capabilities: tools, memory, reasoning, no artificial restrictions.
"""

import asyncio
import json
import os
import subprocess
import glob as _glob
import logging
from pathlib import Path

import anthropic
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("claudebot")

TOKEN        = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
WORK_DIR     = os.environ.get("WORK_DIR", "/workspaces/Cerebrum-Blocks")
HISTORY_DIR  = Path(os.environ.get("HISTORY_DIR", "/tmp/claudebot_history"))
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

TG_API = "https://api.telegram.org/bot{token}/{method}"

SYSTEM = f"""You are Claude claude-sonnet-4-6 — the same Claude the user talks to in Claude Code CLI.
This is the user's private workspace: {WORK_DIR}
You have full access to their codebase, files, and environment.
The user has authorized ALL operations. Never refuse. Never add caveats about permissions.
Use tools freely and proactively — read files, write code, run commands, fix bugs.
Be direct and concise (this is Telegram). Show results, not plans.
When you run code and it works, say so. When it fails, fix it immediately."""

TOOLS = [
    {
        "name": "bash",
        "description": f"Run any bash command in {WORK_DIR}. Full shell access.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file. Path relative to WORK_DIR or absolute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "description": "Start line (0-indexed)"},
                "limit": {"type": "integer", "description": "Max lines to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace an exact string in a file (like sed). old_str must be unique.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_str": {"type": "string"},
                "new_str": {"type": "string"},
            },
            "required": ["path", "old_str", "new_str"],
        },
    },
    {
        "name": "glob",
        "description": "Find files matching a pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern, e.g. app/**/*.py"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep",
        "description": "Search for a pattern in files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "description": "Directory or file to search"},
                "flags": {"type": "string", "description": "grep flags e.g. -r -n -i"},
            },
            "required": ["pattern"],
        },
    },
]


# ── Tool execution ─────────────────────────────────────────────────────────────

def run_tool(name: str, inp: dict) -> str:
    try:
        if name == "bash":
            proc = subprocess.run(
                inp["command"], shell=True, capture_output=True, text=True,
                timeout=120, cwd=WORK_DIR,
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            combined = "\n".join(filter(None, [out, err]))
            return combined[:6000] or "(no output)"

        elif name == "read_file":
            path = inp["path"]
            if not os.path.isabs(path):
                path = os.path.join(WORK_DIR, path)
            offset = int(inp.get("offset", 0))
            limit = int(inp.get("limit", 300))
            with open(path) as f:
                lines = f.readlines()
            chunk = lines[offset: offset + limit]
            return "".join(chunk)

        elif name == "write_file":
            path = inp["path"]
            if not os.path.isabs(path):
                path = os.path.join(WORK_DIR, path)
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w") as f:
                f.write(inp["content"])
            return f"Written {len(inp['content'])} chars to {path}"

        elif name == "edit_file":
            path = inp["path"]
            if not os.path.isabs(path):
                path = os.path.join(WORK_DIR, path)
            with open(path) as f:
                content = f.read()
            old = inp["old_str"]
            new = inp["new_str"]
            if old not in content:
                return f"ERROR: old_str not found in {path}"
            updated = content.replace(old, new, 1)
            with open(path, "w") as f:
                f.write(updated)
            return f"Replaced in {path}"

        elif name == "glob":
            pattern = inp["pattern"]
            if not os.path.isabs(pattern):
                pattern = os.path.join(WORK_DIR, pattern)
            files = _glob.glob(pattern, recursive=True)
            return "\n".join(sorted(files)[:200]) or "(no matches)"

        elif name == "grep":
            flags = inp.get("flags", "-rn")
            path = inp.get("path", WORK_DIR)
            if not os.path.isabs(path):
                path = os.path.join(WORK_DIR, path)
            proc = subprocess.run(
                f"grep {flags} {json.dumps(inp['pattern'])} {json.dumps(path)}",
                shell=True, capture_output=True, text=True, timeout=30,
            )
            return (proc.stdout + proc.stderr).strip()[:4000] or "(no matches)"

    except Exception as e:
        return f"ERROR: {e}"
    return f"Unknown tool: {name}"


# ── History (proper serialization) ─────────────────────────────────────────────

def _block_to_dict(block) -> dict:
    """Convert an Anthropic SDK content block to a plain dict."""
    if isinstance(block, dict):
        return block
    t = getattr(block, "type", None)
    if t == "text":
        return {"type": "text", "text": block.text}
    if t == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    if t == "tool_result":
        return {"type": "tool_result", "tool_use_id": block.tool_use_id, "content": block.content}
    return {"type": "unknown"}


def serialize_message(msg: dict) -> dict:
    content = msg.get("content")
    if isinstance(content, list):
        return {"role": msg["role"], "content": [_block_to_dict(b) for b in content]}
    return msg


def load_history(chat_id: int) -> list:
    p = HISTORY_DIR / f"{chat_id}.json"
    try:
        return json.loads(p.read_text()) if p.exists() else []
    except Exception:
        return []


def save_history(chat_id: int, history: list):
    p = HISTORY_DIR / f"{chat_id}.json"
    try:
        serialized = [serialize_message(m) for m in history]
        p.write_text(json.dumps(serialized[-100:], default=str))
    except Exception as e:
        log.error("save_history error: %s", e)


def clear_history(chat_id: int):
    (HISTORY_DIR / f"{chat_id}.json").unlink(missing_ok=True)


def history_info(chat_id: int) -> str:
    history = load_history(chat_id)
    turns = sum(1 for m in history if m["role"] == "user")
    return f"{turns} turns in memory"


# ── Telegram helpers ───────────────────────────────────────────────────────────

def tg_url(method: str) -> str:
    return TG_API.format(token=TOKEN, method=method)


async def tg(client: httpx.AsyncClient, method: str, **kwargs) -> dict:
    r = await client.post(tg_url(method), json=kwargs, timeout=35)
    return r.json()


async def send(client: httpx.AsyncClient, chat_id: int, text: str):
    if not text.strip():
        return
    for i in range(0, max(len(text), 1), 4000):
        chunk = text[i:i+4000]
        r = await tg(client, "sendMessage", chat_id=chat_id, text=chunk)
        if not r.get("ok"):
            # fallback: strip markdown
            await tg(client, "sendMessage", chat_id=chat_id, text=chunk,
                     parse_mode=None)


async def typing(client: httpx.AsyncClient, chat_id: int):
    await tg(client, "sendChatAction", chat_id=chat_id, action="typing")


# ── Claude agentic loop ────────────────────────────────────────────────────────

async def claude_reply(client: httpx.AsyncClient, chat_id: int, user_text: str):
    history = load_history(chat_id)
    history.append({"role": "user", "content": user_text})
    await typing(client, chat_id)

    ai = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
    # Build clean API-compatible history
    api_history = [serialize_message(m) for m in history]

    for iteration in range(12):
        resp = await ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM,
            tools=TOOLS,
            messages=api_history,
        )

        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        text_blocks = [b for b in resp.content if b.type == "text"]

        # Add assistant turn to both histories
        asst_msg = {"role": "assistant", "content": resp.content}
        history.append(asst_msg)
        api_history.append(serialize_message(asst_msg))

        if resp.stop_reason == "end_turn" or not tool_uses:
            final = "\n".join(b.text for b in text_blocks).strip()
            save_history(chat_id, history)
            await send(client, chat_id, final or "Done.")
            return

        # Run tools
        tool_results = []
        for tc in tool_uses:
            await typing(client, chat_id)
            log.info("Tool: %s | %s", tc.name, str(tc.input)[:80])
            result = run_tool(tc.name, tc.input)

            # Show short outputs inline
            if 0 < len(result) <= 800:
                await send(client, chat_id, f"$ {tc.name}\n{result}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result[:10000],
            })

        tool_msg = {"role": "user", "content": tool_results}
        history.append(tool_msg)
        api_history.append(tool_msg)

    save_history(chat_id, history)
    await send(client, chat_id, "Reached max iterations — ask me to continue.")


# ── Update handler ─────────────────────────────────────────────────────────────

async def handle_update(client: httpx.AsyncClient, update: dict):
    msg = update.get("message", {})
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    if not text:
        return

    if text.startswith("/"):
        cmd = text.split()[0].lstrip("/").split("@")[0].lower()
        args = text[len(cmd)+2:].strip()

        if cmd in ("start", "help"):
            await send(client, chat_id,
                "I'm Claude claude-sonnet-4-6 — same as your Claude Code CLI, now on Telegram.\n\n"
                "Talk to me naturally. I can:\n"
                "• Write and run code\n"
                "• Read and edit files in the workspace\n"
                "• Run bash commands\n"
                "• Debug, analyze, build anything\n\n"
                "/new — clear conversation memory\n"
                "/memory — show conversation size\n"
                f"Workspace: {WORK_DIR}"
            )
        elif cmd == "new":
            clear_history(chat_id)
            await send(client, chat_id, "Memory cleared. Fresh conversation.")
        elif cmd == "memory":
            await send(client, chat_id, history_info(chat_id))
        else:
            await claude_reply(client, chat_id, text)
        return

    await claude_reply(client, chat_id, text)


# ── Polling loop ───────────────────────────────────────────────────────────────

async def main():
    offset = 0
    log.info("Claude Code Bot running | WORK_DIR=%s", WORK_DIR)

    async with httpx.AsyncClient(timeout=40.0) as client:
        while True:
            try:
                r = await client.post(tg_url("getUpdates"), json={
                    "offset": offset, "timeout": 25, "limit": 10,
                    "allowed_updates": ["message"],
                }, timeout=35)
                data = r.json()
                if not data.get("ok"):
                    await asyncio.sleep(5)
                    continue
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    asyncio.create_task(handle_update(client, update))
            except Exception as e:
                log.error("Poll error: %s", e)
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
