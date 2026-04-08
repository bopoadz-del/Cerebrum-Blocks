import { useState } from "react";

const todos = [
  {
    id: 1,
    title: "Rename GitHub Repo",
    time: "2 min",
    priority: "CRITICAL",
    color: "#ff4444",
    description: "SSDPPG is your wind energy patent. This repo needs a developer-friendly name.",
    steps: [
      "Go to github.com/bopoadz-del/SSDPPG",
      "Settings → scroll to bottom → Danger Zone",
      'Click "Rename" → type cerebrum-blocks → confirm',
      "Update your local clone: git remote set-url origin https://github.com/bopoadz-del/cerebrum-blocks",
    ],
    code: null,
    lang: null,
  },
  {
    id: 2,
    title: "Add Streaming to Chat Block",
    time: "1 hour",
    priority: "HIGH",
    color: "#ff8800",
    description: "Replace the one-shot response with real-time word-by-word streaming using FastAPI StreamingResponse.",
    steps: [
      "Open app/blocks/chat.py",
      "Replace the execute() method with the streaming version below",
      "Add the /stream endpoint to app/main.py",
      "Test with: curl -N http://localhost:8000/stream",
    ],
    code: `# app/blocks/chat.py — replace your execute() method

import json
from fastapi.responses import StreamingResponse

class ChatBlock:

    async def stream(self, message: str, provider: str = "groq"):
        \"\"\"Stream response chunk by chunk\"\"\"
        import httpx

        url = self._get_endpoint(provider)
        headers = self._get_headers(provider)

        body = {
            "model": self._get_model(provider),
            "messages": [{"role": "user", "content": message}],
            "stream": True,
            "max_tokens": 1024,
        }

        async def generate():
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", url, headers=headers, json=body) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\\n\\n"
                            except Exception:
                                continue

        return StreamingResponse(generate(), media_type="text/event-stream")


# app/main.py — add this endpoint

@app.post("/stream")
async def stream_chat(request: dict):
    block = ChatBlock()
    return await block.stream(
        message=request.get("input", ""),
        provider=request.get("params", {}).get("provider", "groq")
    )`,
    lang: "python",
  },
  {
    id: 3,
    title: "Add API Key Authentication",
    time: "3–4 hours",
    priority: "HIGH",
    color: "#ff8800",
    description: "Without this you cannot charge, cannot control abuse, cannot track usage. This is the business layer.",
    steps: [
      "Create a simple SQLite DB (or use Redis) to store keys",
      "Add the middleware below to app/main.py",
      "Generate keys with secrets.token_urlsafe(32)",
      "Every request must include: Authorization: Bearer cb_xxxxx",
    ],
    code: `# app/middleware/auth.py — create this file

import sqlite3
import secrets
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware

DB_PATH = "data/keys.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            name TEXT,
            calls_used INTEGER DEFAULT 0,
            calls_limit INTEGER DEFAULT 1000,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def generate_key(name: str, limit: int = 1000) -> str:
    key = "cb_" + secrets.token_urlsafe(32)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO api_keys (key, name, calls_limit) VALUES (?, ?, ?)",
        (key, name, limit)
    )
    conn.commit()
    conn.close()
    return key

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer cb_"):
            raise HTTPException(status_code=401, detail="Missing or invalid API key")

        key = auth.replace("Bearer ", "")
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT calls_used, calls_limit, active FROM api_keys WHERE key = ?",
            (key,)
        ).fetchone()

        if not row or not row[2]:
            raise HTTPException(status_code=401, detail="Invalid API key")
        if row[0] >= row[1]:
            raise HTTPException(status_code=429, detail="Usage limit reached")

        conn.execute(
            "UPDATE api_keys SET calls_used = calls_used + 1 WHERE key = ?", (key,)
        )
        conn.commit()
        conn.close()

        return await call_next(request)


# app/main.py — add these lines at the top after creating app

from app.middleware.auth import APIKeyMiddleware, init_db, generate_key

init_db()
app.add_middleware(APIKeyMiddleware)

# Temporary admin endpoint to generate keys (protect this later!)
@app.post("/admin/generate-key")
def create_key(name: str, limit: int = 1000):
    key = generate_key(name, limit)
    return {"key": key, "name": name, "limit": limit}`,
    lang: "python",
  },
  {
    id: 4,
    title: "Deploy to Render with Custom Domain",
    time: "1 hour",
    priority: "HIGH",
    color: "#ff8800",
    description: "One hosted endpoint that every developer calls. This is what makes it plug-and-play instead of DIY.",
    steps: [
      "Push all changes to GitHub",
      "Go to render.com → New Web Service → connect cerebrum-blocks repo",
      "Set build command and start command (see below)",
      "Add environment variables in Render dashboard",
      "Add a custom domain: api.cerebrumblocks.com",
    ],
    code: `# render.yaml — already in your repo, update it to this:

services:
  - type: web
    name: cerebrum-blocks-api
    env: python
    plan: starter          # $7/month
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATA_DIR
        value: /app/data
      - key: GROQ_API_KEY
        sync: false        # Set manually in Render dashboard
      - key: OPENAI_API_KEY
        sync: false
    disk:
      name: data
      mountPath: /app/data
      sizeGB: 1


# .env.example — update with all required keys:

PORT=8000
DATA_DIR=./data
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
CHROMA_PERSIST_DIR=./data/chroma_db`,
    lang: "yaml",
  },
  {
    id: 5,
    title: "Publish Python Package to PyPI",
    time: "1–2 hours",
    priority: "MEDIUM",
    color: "#00aaff",
    description: "So developers can pip install cerebrum-blocks instead of cloning your repo.",
    steps: [
      "Create account at pypi.org",
      "pip install build twine",
      "python -m build",
      "twine upload dist/*",
      "Done: pip install cerebrum-blocks works globally",
    ],
    code: `# packages/python/setup.py — final version

from setuptools import setup, find_packages

setup(
    name="cerebrum-blocks",
    version="0.1.0",
    description="Plug-and-play AI building blocks. 3 lines of code.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Chadi Mahmoud",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",    # For async HTTP + streaming
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)


# Build and publish commands:
# pip install build twine
# python -m build
# twine upload dist/*


# After publishing, developers install with:
# pip install cerebrum-blocks

# And use it:
from cerebrum_blocks import CerebrumChat

chat = CerebrumChat(api_key="cb_your_key_here")
for chunk in chat.stream("Tell me about AI"):
    print(chunk, end="", flush=True)`,
    lang: "python",
  },
  {
    id: 6,
    title: "Publish JS SDK to npm",
    time: "1 hour",
    priority: "MEDIUM",
    color: "#00aaff",
    description: "The SDK we built today. Publish it so any JavaScript developer can install in one command.",
    steps: [
      "Create account at npmjs.com",
      "cd packages/js",
      "npm login",
      "npm run build (compiles TypeScript)",
      "npm publish --access public",
    ],
    code: `# Terminal commands to publish:

cd packages/js
npm login
npm run build
npm publish --access public


# After publishing, developers install with:
# npm install cerebrum-blocks

# And use it in 3 lines:
import { CerebrumChat } from 'cerebrum-blocks'

const chat = new CerebrumChat({ apiKey: 'cb_your_key_here' })

for await (const chunk of chat.stream("Explain quantum computing")) {
  process.stdout.write(chunk)
}


# packages/js/package.json — make sure these fields are correct:
{
  "name": "cerebrum-blocks",
  "version": "0.1.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": ["dist"],
  "publishConfig": {
    "access": "public"
  }
}`,
    lang: "bash",
  },
  {
    id: 7,
    title: "Rewrite the README",
    time: "30 min",
    priority: "MEDIUM",
    color: "#00aaff",
    description: "Current README reads like internal docs. Developers decide in 8 seconds. Lead with the 3-line install.",
    steps: [
      "Open README.md",
      "Delete everything",
      "Start with the structure below",
      "Add your Render deployment URL to the examples",
    ],
    code: `# README.md — new structure:

# 🧠 Cerebrum Blocks
> Plug-and-play AI building blocks. Every environment. 3 lines of code.

## Install
\`\`\`bash
npm install cerebrum-blocks     # JavaScript
pip install cerebrum-blocks     # Python
\`\`\`

## Quickstart
\`\`\`javascript
import { CerebrumChat } from 'cerebrum-blocks'

const chat = new CerebrumChat({ apiKey: 'cb_your_key' })

for await (const chunk of chat.stream("Explain AI")) {
  process.stdout.write(chunk)
}
\`\`\`

## Get an API Key
→ cerebrumblocks.com/signup

## 13 Blocks Available
Chat · OCR · Voice · PDF · Vector Search · 
Image · Translate · Code · Web · 
Google Drive · OneDrive · Local Drive · Android Drive

## Full Docs
→ docs.cerebrumblocks.com`,
    lang: "markdown",
  },
];

const priorityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2 };

export default function TodoGuide() {
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState(false);

  const todo = todos[active];

  const copy = () => {
    if (todo.code) {
      navigator.clipboard.writeText(todo.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      background: "#0a0a0f",
      minHeight: "100vh",
      color: "#e0e0e0",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Header */}
      <div style={{
        borderBottom: "1px solid #1e1e2e",
        padding: "20px 28px",
        display: "flex",
        alignItems: "center",
        gap: 14,
        background: "#0d0d18",
      }}>
        <div style={{
          width: 36, height: 36,
          background: "linear-gradient(135deg, #6c63ff, #3ec6ff)",
          borderRadius: 8,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18, fontWeight: 900,
        }}>🧠</div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", letterSpacing: 1 }}>CEREBRUM BLOCKS</div>
          <div style={{ fontSize: 11, color: "#555", letterSpacing: 2 }}>LAUNCH TODO — 7 TASKS · EST. 1 WEEKEND</div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {["CRITICAL","HIGH","MEDIUM"].map(p => (
            <div key={p} style={{
              fontSize: 10, letterSpacing: 1.5,
              padding: "3px 10px", borderRadius: 4,
              border: `1px solid ${p==="CRITICAL"?"#ff4444":p==="HIGH"?"#ff8800":"#00aaff"}`,
              color: p==="CRITICAL"?"#ff4444":p==="HIGH"?"#ff8800":"#00aaff",
            }}>{p}</div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Sidebar */}
        <div style={{
          width: 280, borderRight: "1px solid #1e1e2e",
          overflowY: "auto", background: "#0d0d18",
          flexShrink: 0,
        }}>
          {todos.map((t, i) => (
            <div
              key={t.id}
              onClick={() => setActive(i)}
              style={{
                padding: "16px 20px",
                borderBottom: "1px solid #1a1a2a",
                cursor: "pointer",
                background: active === i ? "#151525" : "transparent",
                borderLeft: active === i ? `3px solid ${t.color}` : "3px solid transparent",
                transition: "all 0.15s",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <div style={{
                  width: 22, height: 22, borderRadius: "50%",
                  background: active === i ? t.color : "#1e1e2e",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 700,
                  color: active === i ? "#000" : "#555",
                  flexShrink: 0,
                }}>{t.id}</div>
                <div style={{
                  fontSize: 12, fontWeight: 600,
                  color: active === i ? "#fff" : "#888",
                  lineHeight: 1.3,
                }}>{t.title}</div>
              </div>
              <div style={{ display: "flex", gap: 8, paddingLeft: 32 }}>
                <span style={{
                  fontSize: 9, letterSpacing: 1.2, padding: "2px 6px",
                  borderRadius: 3,
                  background: `${t.color}22`,
                  color: t.color,
                }}>{t.priority}</span>
                <span style={{ fontSize: 10, color: "#444" }}>⏱ {t.time}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "32px 36px" }}>
          {/* Task Header */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 10 }}>
              <div style={{
                width: 40, height: 40, borderRadius: "50%",
                background: `${todo.color}22`,
                border: `2px solid ${todo.color}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 16, fontWeight: 800, color: todo.color,
              }}>{todo.id}</div>
              <div>
                <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: "#fff" }}>{todo.title}</h2>
                <div style={{ fontSize: 11, color: "#555", marginTop: 3 }}>
                  <span style={{ color: todo.color }}>{todo.priority}</span>
                  <span style={{ margin: "0 8px" }}>·</span>
                  <span>⏱ {todo.time}</span>
                </div>
              </div>
            </div>
            <p style={{
              margin: 0, fontSize: 13, color: "#888",
              lineHeight: 1.7, paddingLeft: 54,
            }}>{todo.description}</p>
          </div>

          {/* Steps */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 11, letterSpacing: 2, color: "#444", marginBottom: 14 }}>STEPS</div>
            {todo.steps.map((step, i) => (
              <div key={i} style={{
                display: "flex", gap: 14, marginBottom: 12, alignItems: "flex-start",
              }}>
                <div style={{
                  width: 24, height: 24, borderRadius: "50%",
                  border: `1px solid ${todo.color}44`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, color: todo.color, flexShrink: 0, marginTop: 1,
                }}>{i + 1}</div>
                <div style={{ fontSize: 13, color: "#bbb", lineHeight: 1.6 }}>{step}</div>
              </div>
            ))}
          </div>

          {/* Code Block */}
          {todo.code && (
            <div>
              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                marginBottom: 10,
              }}>
                <div style={{ fontSize: 11, letterSpacing: 2, color: "#444" }}>CODE</div>
                <button
                  onClick={copy}
                  style={{
                    background: copied ? "#00aa6622" : "#1e1e2e",
                    border: `1px solid ${copied ? "#00aa66" : "#2e2e3e"}`,
                    color: copied ? "#00aa66" : "#666",
                    fontSize: 11, padding: "5px 14px", borderRadius: 4,
                    cursor: "pointer", letterSpacing: 1, fontFamily: "inherit",
                    transition: "all 0.2s",
                  }}
                >{copied ? "✓ COPIED" : "COPY"}</button>
              </div>
              <div style={{
                background: "#080810",
                border: "1px solid #1e1e2e",
                borderRadius: 8,
                padding: "20px 24px",
                overflowX: "auto",
              }}>
                <pre style={{
                  margin: 0, fontSize: 12, lineHeight: 1.8,
                  color: "#c9d1d9", whiteSpace: "pre-wrap", wordBreak: "break-word",
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                }}>
                  {todo.code.split("\n").map((line, i) => {
                    let color = "#c9d1d9";
                    if (line.trim().startsWith("#")) color = "#6a9955";
                    else if (line.includes("def ") || line.includes("class ") || line.includes("async def")) color = "#dcdcaa";
                    else if (line.includes("import ") || line.includes("from ")) color = "#c586c0";
                    else if (line.includes('"') || line.includes("'")) color = "#ce9178";
                    return (
                      <span key={i} style={{ display: "block", color }}>
                        {line || " "}
                      </span>
                    );
                  })}
                </pre>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div style={{
            display: "flex", justifyContent: "space-between", marginTop: 40,
            paddingTop: 24, borderTop: "1px solid #1e1e2e",
          }}>
            <button
              onClick={() => setActive(Math.max(0, active - 1))}
              disabled={active === 0}
              style={{
                background: "transparent", border: "1px solid #2e2e3e",
                color: active === 0 ? "#2e2e3e" : "#888",
                padding: "8px 20px", borderRadius: 4,
                cursor: active === 0 ? "default" : "pointer",
                fontSize: 12, fontFamily: "inherit", letterSpacing: 1,
              }}
            >← PREV</button>
            <span style={{ fontSize: 11, color: "#333", alignSelf: "center" }}>
              {active + 1} / {todos.length}
            </span>
            <button
              onClick={() => setActive(Math.min(todos.length - 1, active + 1))}
              disabled={active === todos.length - 1}
              style={{
                background: active === todos.length - 1 ? "transparent" : todos[active].color,
                border: `1px solid ${active === todos.length - 1 ? "#2e2e3e" : todos[active].color}`,
                color: active === todos.length - 1 ? "#2e2e3e" : "#000",
                padding: "8px 20px", borderRadius: 4,
                cursor: active === todos.length - 1 ? "default" : "pointer",
                fontSize: 12, fontWeight: 700, fontFamily: "inherit", letterSpacing: 1,
              }}
            >NEXT →</button>
          </div>
        </div>
      </div>
    </div>
  );
}
