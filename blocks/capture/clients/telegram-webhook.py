#!/usr/bin/env python3
"""Telegram Bot webhook handler for Cerebrum Capture Block.

Deploy this as a FastAPI route or serverless function.
Receives photo messages from Telegram, downloads image, forwards to Capture Block.

Usage:
    export TELEGRAM_BOT_TOKEN=your_token
    export CAPTURE_API_URL=https://your-server/capture/upload
    export CEREBRUM_API_KEY=your_key
    python telegram-webhook.py
"""

import os
import io
import sys
import httpx
from fastapi import FastAPI, Request

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CAPTURE_API_URL = os.getenv("CAPTURE_API_URL", "http://localhost:8000/capture/upload")
API_KEY = os.getenv("CEREBRUM_API_KEY", "")

app = FastAPI()


def _tg_url(method: str) -> str:
    return TELEGRAM_API.format(token=BOT_TOKEN, method=method)


async def _download_photo(file_path: str) -> bytes:
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def _send_message(chat_id: int, text: str):
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(_tg_url("sendMessage"), json={"chat_id": chat_id, "text": text})


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    photo = message.get("photo")

    if not photo or not chat_id:
        return {"ok": True, "action": "ignored"}

    # Get largest photo
    largest = max(photo, key=lambda p: p.get("file_size", 0))
    file_id = largest["file_id"]

    await _send_message(chat_id, "⏳ Processing capture...")

    # Get file path from Telegram
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(_tg_url("getFile"), json={"file_id": file_id})
        file_info = resp.json()

    if not file_info.get("ok"):
        await _send_message(chat_id, "❌ Failed to get photo from Telegram.")
        return {"ok": False}

    tg_file_path = file_info["result"]["file_path"]
    image_bytes = await _download_photo(tg_file_path)

    # Forward to Capture Block
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            files = {"file": ("photo.jpg", io.BytesIO(image_bytes), "image/jpeg")}
            data = {"source": "telegram", "user_id": str(chat_id)}
            headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
            resp = await client.post(CAPTURE_API_URL, data=data, files=files, headers=headers)
            result = resp.json()
    except Exception as e:
        await _send_message(chat_id, f"❌ Capture Block error: {e}")
        return {"ok": False}

    # Reply with structured result
    capture_id = result.get("capture_id", "N/A")
    summary = result.get("summary", "")
    tags = ", ".join(result.get("tags", []))
    entities = result.get("entities", [])

    reply = (
        f"✅ *Capture Uploaded*\n"
        f"*ID:* `{capture_id}`\n"
        f"*Summary:* {summary}\n"
        f"*Tags:* {tags}\n"
    )
    if entities:
        reply += "*Entities:*\n"
        for ent in entities[:5]:
            reply += f"  • {ent.get('type', 'unknown')}: `{ent.get('value', '')}`\n"

    await _send_message(chat_id, reply)
    return {"ok": True, "capture_id": capture_id}


if __name__ == "__main__":
    import uvicorn

    if not BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "9000")))
