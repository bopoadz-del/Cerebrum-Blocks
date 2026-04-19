"""
Claude Code Telegram Bot
Prereqs: Python 3.11+, Claude Code CLI, Telegram Bot Token
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path

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

TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
WORK_DIR   = os.environ.get("WORK_DIR", "/workspaces/Cerebrum-Blocks")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
SESSIONS   = Path(os.environ.get("SESSIONS_DIR", "/tmp/claudebot_sessions"))
SESSIONS.mkdir(parents=True, exist_ok=True)

_allowed   = os.environ.get("ALLOWED_USERS", "")
ALLOWED_USERS = {int(x.strip()) for x in _allowed.split(",") if x.strip()}


# ── Session persistence ────────────────────────────────────────────────────────

def load_session(chat_id: int) -> str | None:
    f = SESSIONS / f"{chat_id}.session"
    return f.read_text().strip() if f.exists() else None

def save_session(chat_id: int, sid: str):
    (SESSIONS / f"{chat_id}.session").write_text(sid)

def clear_session(chat_id: int):
    (SESSIONS / f"{chat_id}.session").unlink(missing_ok=True)


# ── Claude CLI ─────────────────────────────────────────────────────────────────

async def run_claude(chat_id: int, message: str) -> str:
    session_id = load_session(chat_id)

    cmd = [
        CLAUDE_BIN,
        "--print",
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]
    if session_id:
        cmd += ["--resume", session_id]
    cmd.append(message)

    loop = asyncio.get_event_loop()
    try:
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=300, cwd=WORK_DIR,
            ),
        )
    except subprocess.TimeoutExpired:
        return "Timed out after 5 minutes."
    except Exception as e:
        return f"Error running Claude CLI: {e}"

    if proc.returncode != 0:
        return proc.stderr.strip() or "Claude CLI returned an error."

    try:
        data = json.loads(proc.stdout)
        if sid := data.get("session_id"):
            save_session(chat_id, sid)
        return data.get("result", "").strip() or "(no output)"
    except Exception:
        return proc.stdout.strip() or "(no output)"


# ── Handlers ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Claude Code on Telegram — full capabilities.\n\n"
        "Read/write files, run bash, edit code, commit to GitHub.\n"
        f"Workspace: {WORK_DIR}\n\n"
        "/new — start a fresh session"
    )

async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_session(update.effective_chat.id)
    await update.message.reply_text("Session cleared — fresh start.")

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
        reply = await run_claude(chat_id, text)
    except Exception as e:
        reply = f"Error: {e}"
    finally:
        stop_flag.set()
        typing_task.cancel()

    for i in range(0, max(len(reply), 1), 4000):
        await update.message.reply_text(reply[i : i + 4000])


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("Claude Code Bot | workspace=%s cli=%s", WORK_DIR, CLAUDE_BIN)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler(["new", "clear"], cmd_new))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
