"""
Claude Code Telegram Bot — Full agentic capabilities via Telegram.
Follows https://github.com/RichardAtCT/claude-code-telegram pattern:
  - python-telegram-bot for Telegram handling
  - Anthropic SDK with tool execution (agentic loop)
  - Persistent conversation history per chat
"""

import asyncio
import glob
import json
import logging
import os
import subprocess
from pathlib import Path

import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("claudebot")

TOKEN         = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
WORK_DIR      = os.environ.get("WORK_DIR", "/workspaces/Cerebrum-Blocks")
MODEL         = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

_allowed_raw  = os.environ.get("ALLOWED_USERS", "")
ALLOWED_USERS = {int(x.strip()) for x in _allowed_raw.split(",") if x.strip()}

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# In-memory history per chat_id
histories: dict[int, list] = {}

SYSTEM = (
    f"You are Claude Code — the user's personal AI on Telegram with full capabilities.\n"
    f"Working directory: {WORK_DIR}\n"
    f"You can read/write files, run bash, edit code, commit and push to GitHub.\n"
    f"ALL operations are pre-authorized by the workspace owner.\n"
    f"Be concise — this is Telegram. Use plain text."
)

TOOLS = [
    {
        "name": "bash",
        "description": "Run a bash command in the working directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"}
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the full contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to WORK_DIR or absolute)"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace an exact string in a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":       {"type": "string"},
                "old_string": {"type": "string", "description": "Exact text to find"},
                "new_string": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "list_files",
        "description": "List files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern, e.g. **/*.py"}
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "search_code",
        "description": "Search for a regex pattern in files (ripgrep).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex to search for"},
                "path":    {"type": "string", "description": "Directory to search (default: WORK_DIR)"},
            },
            "required": ["pattern"],
        },
    },
]


# ── Tool execution ─────────────────────────────────────────────────────────────

def _resolve(path: str) -> Path:
    p = Path(path)
    return (Path(WORK_DIR) / p).resolve() if not p.is_absolute() else p.resolve()


def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "bash":
            r = subprocess.run(
                inputs["command"], shell=True, capture_output=True, text=True,
                timeout=120, cwd=WORK_DIR,
            )
            out = r.stdout
            if r.stderr:
                out += f"\nSTDERR:\n{r.stderr}"
            return out.strip() or "(no output)"

        if name == "read_file":
            return _resolve(inputs["path"]).read_text()

        if name == "write_file":
            p = _resolve(inputs["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(inputs["content"])
            return f"Written {p}"

        if name == "edit_file":
            p = _resolve(inputs["path"])
            text = p.read_text()
            if inputs["old_string"] not in text:
                return f"ERROR: old_string not found in {p}"
            p.write_text(text.replace(inputs["old_string"], inputs["new_string"], 1))
            return f"Edited {p}"

        if name == "list_files":
            matches = glob.glob(inputs["pattern"], root_dir=WORK_DIR, recursive=True)
            return "\n".join(matches) or "(no matches)"

        if name == "search_code":
            search_path = inputs.get("path", WORK_DIR)
            r = subprocess.run(
                ["rg", "-l", inputs["pattern"], search_path],
                capture_output=True, text=True, cwd=WORK_DIR, timeout=30,
            )
            return r.stdout.strip() or "(no matches)"

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"


# ── Agentic loop ───────────────────────────────────────────────────────────────

async def run_agent(chat_id: int, user_message: str) -> str:
    history = histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_message})

    loop = asyncio.get_event_loop()

    for _ in range(30):
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model=MODEL,
                max_tokens=8096,
                system=SYSTEM,
                tools=TOOLS,
                messages=history,
            ),
        )

        # Build assistant turn
        assistant_content = []
        tool_uses = []
        text_parts = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_uses.append(block)
                assistant_content.append({
                    "type": "tool_use",
                    "id":    block.id,
                    "name":  block.name,
                    "input": block.input,
                })

        history.append({"role": "assistant", "content": assistant_content})

        if not tool_uses or response.stop_reason == "end_turn":
            result = "\n".join(text_parts).strip()
            return result or "(done)"

        # Execute all tool calls
        tool_results = []
        for tu in tool_uses:
            log.info("tool=%s chat=%s", tu.name, chat_id)
            result = await loop.run_in_executor(None, lambda t=tu: execute_tool(t.name, t.input))
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tu.id,
                "content":     result[:12000],
            })

        history.append({"role": "user", "content": tool_results})

    return "Reached maximum iterations."


def _trim_history(chat_id: int, max_turns: int = 50):
    h = histories.get(chat_id, [])
    if len(h) > max_turns:
        histories[chat_id] = h[-max_turns:]


# ── Telegram handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Claude Code on Telegram — full capabilities.\n\n"
        f"Read/write files, run bash, edit code, commit to GitHub.\n"
        f"Workspace: {WORK_DIR}\n\n"
        f"/new — clear session"
    )


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    histories.pop(update.effective_chat.id, None)
    await update.message.reply_text("Session cleared.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if ALLOWED_USERS and user.id not in ALLOWED_USERS:
        await update.message.reply_text("Not authorized.")
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    log.info("chat=%s user=%s | %s", chat_id, user.id, text[:80])

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    stop_flag = asyncio.Event()

    async def keep_typing():
        while not stop_flag.is_set():
            await asyncio.sleep(4)
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception:
                pass

    typing_task = asyncio.create_task(keep_typing())
    try:
        reply = await run_agent(chat_id, text)
    except Exception as e:
        reply = f"Error: {e}"
        log.exception("Agent error chat=%s", chat_id)
    finally:
        stop_flag.set()
        typing_task.cancel()

    _trim_history(chat_id)

    for i in range(0, max(len(reply), 1), 4000):
        await update.message.reply_text(reply[i : i + 4000])


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    log.info("Claude Code Bot | workspace=%s model=%s", WORK_DIR, MODEL)

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler(["new", "clear"], cmd_new))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
