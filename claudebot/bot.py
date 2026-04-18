"""
Claude Code Bot — Standalone Telegram agent powered by Claude claude-sonnet-4-6
Runs independently, no Cerebrum platform dependency.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("claudebot")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
TOKEN        = os.environ["TELEGRAM_BOT_TOKEN"]
WORK_DIR     = os.environ.get("WORK_DIR", str(Path.home()))
HISTORY_DIR  = Path(os.environ.get("HISTORY_DIR", "/tmp/claudebot_history"))
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are Claude — a highly capable AI assistant and coding agent.
You have access to tools: run_python, run_bash, read_file, write_file, list_files.
Use them freely to help the user. Be concise in Telegram (no heavy markdown).
When writing code, run it and show the result. When editing files, confirm what changed."""

TOOLS = [
    {
        "name": "run_python",
        "description": "Execute Python code. Returns stdout/stderr.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
    {
        "name": "run_bash",
        "description": "Run a bash command in WORK_DIR. Returns stdout/stderr.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
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
                "lines": {"type": "integer", "description": "Max lines (default 200)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
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
        "name": "list_files",
        "description": "List files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": ["pattern"],
        },
    },
]


def execute_tool(name: str, inp: dict) -> str:
    try:
        if name == "run_python":
            proc = subprocess.run(
                ["python", "-c", inp["code"]],
                capture_output=True, text=True, timeout=30, cwd=WORK_DIR,
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            return f"{out}\n{err}".strip() or "(no output)"

        elif name == "run_bash":
            proc = subprocess.run(
                inp["command"], shell=True, capture_output=True, text=True,
                timeout=60, cwd=WORK_DIR,
            )
            return (proc.stdout.strip() + "\n" + proc.stderr.strip()).strip()[:4000] or "(no output)"

        elif name == "read_file":
            path = inp["path"]
            if not os.path.isabs(path):
                path = os.path.join(WORK_DIR, path)
            lines = int(inp.get("lines", 200))
            with open(path) as f:
                content = f.readlines()
            return "".join(content[:lines])

        elif name == "write_file":
            path = inp["path"]
            if not os.path.isabs(path):
                path = os.path.join(WORK_DIR, path)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(inp["content"])
            return f"Written {len(inp['content'])} chars to {path}"

        elif name == "list_files":
            pattern = inp["pattern"]
            if not os.path.isabs(pattern):
                pattern = os.path.join(WORK_DIR, pattern)
            files = _glob.glob(pattern, recursive=True)
            return "\n".join(sorted(files)[:100]) or "(no matches)"

    except Exception as e:
        return f"ERROR: {e}"
    return "Unknown tool"


# ── Telegram API ───────────────────────────────────────────────────────────────

def tg_url(method: str) -> str:
    return TELEGRAM_API.format(token=TOKEN, method=method)


async def tg(client: httpx.AsyncClient, method: str, **kwargs) -> dict:
    r = await client.post(tg_url(method), json=kwargs, timeout=30)
    return r.json()


async def send(client: httpx.AsyncClient, chat_id: int, text: str):
    max_len = 4000
    for i in range(0, max(len(text), 1), max_len):
        await tg(client, "sendMessage", chat_id=chat_id, text=text[i:i+max_len])


async def typing(client: httpx.AsyncClient, chat_id: int):
    await tg(client, "sendChatAction", chat_id=chat_id, action="typing")


# ── History ────────────────────────────────────────────────────────────────────

def load_history(chat_id: int) -> list:
    p = HISTORY_DIR / f"{chat_id}.json"
    try:
        return json.loads(p.read_text()) if p.exists() else []
    except Exception:
        return []


def save_history(chat_id: int, history: list):
    p = HISTORY_DIR / f"{chat_id}.json"
    try:
        p.write_text(json.dumps(history[-80:]))
    except Exception:
        pass


def clear_history(chat_id: int):
    p = HISTORY_DIR / f"{chat_id}.json"
    p.unlink(missing_ok=True)


# ── Claude agentic loop ────────────────────────────────────────────────────────

async def claude_chat(client: httpx.AsyncClient, chat_id: int, user_text: str):
    history = load_history(chat_id)
    history.append({"role": "user", "content": user_text})

    await typing(client, chat_id)

    ai = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    for _ in range(10):
        resp = await ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )

        tool_calls = [b for b in resp.content if b.type == "tool_use"]
        text_parts = [b.text for b in resp.content if b.type == "text"]

        history.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn" or not tool_calls:
            final = "\n".join(text_parts).strip()
            save_history(chat_id, history)
            await send(client, chat_id, final or "Done.")
            return

        # Execute tools, show user what's running
        tool_results = []
        for tc in tool_calls:
            await send(client, chat_id, f"🔧 {tc.name}...")
            await typing(client, chat_id)
            result_str = execute_tool(tc.name, tc.input)
            # Show tool output if short enough to be useful
            if len(result_str) < 500 and result_str != "(no output)":
                await send(client, chat_id, f"```\n{result_str}\n```")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result_str[:8000],
            })

        history.append({"role": "user", "content": tool_results})

    save_history(chat_id, history)
    await send(client, chat_id, "Reached max iterations.")


# ── Update handler ─────────────────────────────────────────────────────────────

async def handle_update(client: httpx.AsyncClient, update: dict):
    msg = update.get("message", {})
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    if not text:
        await send(client, chat_id, "Send me text or a command. /help for options.")
        return

    # Commands
    if text.startswith("/"):
        cmd = text.split()[0].lstrip("/").split("@")[0].lower()
        args = text.split(None, 1)[1] if len(text.split(None, 1)) > 1 else ""

        if cmd in ("start",):
            await send(client, chat_id,
                "Hi! I'm Claude — your AI coding assistant.\n\n"
                "Talk to me like you would in Claude Code:\n"
                "• Ask questions\n"
                "• Ask me to write or fix code\n"
                "• Ask me to run commands or read files\n\n"
                "/new — clear conversation history\n"
                "/help — this message"
            )
        elif cmd == "help":
            await send(client, chat_id,
                "Commands:\n"
                "/new — start fresh conversation\n\n"
                "Just type anything else and I'll respond like Claude Code.\n"
                f"Working directory: {WORK_DIR}"
            )
        elif cmd == "new":
            clear_history(chat_id)
            await send(client, chat_id, "Conversation cleared. Fresh start!")
        else:
            # Treat unknown commands as regular messages
            await claude_chat(client, chat_id, text)
        return

    # Regular message → Claude
    await claude_chat(client, chat_id, text)


# ── Polling loop ───────────────────────────────────────────────────────────────

async def poll_loop():
    offset = 0
    log.info("Claude Code Bot started — polling Telegram")
    log.info(f"WORK_DIR: {WORK_DIR}")

    async with httpx.AsyncClient(timeout=40.0) as client:
        while True:
            try:
                r = await client.post(tg_url("getUpdates"), json={
                    "offset": offset, "timeout": 25, "limit": 10,
                    "allowed_updates": ["message"],
                }, timeout=35)
                data = r.json()

                if not data.get("ok"):
                    log.warning("getUpdates not ok: %s", data)
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    try:
                        await handle_update(client, update)
                    except Exception as e:
                        log.error("handle_update error: %s", e)

            except Exception as e:
                log.error("Poll error: %s", e)
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(poll_loop())
