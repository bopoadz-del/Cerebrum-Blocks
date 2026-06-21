"""Chat Block — Qwen primary with OpenAI-compatible fallbacks.

The chat must never go completely dark on the user. Order of attempts:

1. **Qwen API (DashScope)** when ``QWEN_API_KEY`` is set and the endpoint is
   reachable. Configure via ``QWEN_BASE_URL`` and ``QWEN_MODEL``.
2. **Groq** when ``GROQ_API_KEY`` is set.
3. **DeepSeek** when ``DEEPSEEK_API_KEY`` is set.
4. **Local LLM** (kept *inside* the platform — no third-party cloud) via:
   - Ollama HTTP at ``OLLAMA_URL`` (default ``http://localhost:11434``) when a
     local model is installed. The default local model is
     ``LOCAL_LLM_MODEL`` (default ``qwen2.5:3b-instruct`` — small, CPU-runnable).
   - llama.cpp via ``LLAMA_CPP_MODEL_PATH`` when ``llama-cpp-python`` is
     importable and a GGUF file is provided.
5. **Graceful template responder** — a deterministic, non-AI fallback that
   acknowledges the question, surfaces the reason the model layer is down,
   and points the operator at the env vars that would restore it. This
   path always succeeds, so the chat never returns an unhandled error.

The block exposes a single ``provider`` field on the response so callers can
see which path served the answer (``qwen`` / ``groq`` / ``deepseek`` /
``local_ollama`` / ``local_llama_cpp`` / ``offline_template``).
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from app.core.typed_block import TypedBlock, Schema, ContentType


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_LOCAL_MODEL = "qwen2.5:3b-instruct"


class ChatBlock(TypedBlock):
    """AI chat completions — DeepSeek with local-inference fallback."""

    auto_validate = False
    name = "chat"
    version = "3.0.0"
    description = "AI chat completions — DeepSeek primary, local LLM fallback"
    layer = 2
    tags = ["ai", "core", "llm", "chat", "typed"]
    requires = []

    default_config = {
        "default_provider": "qwen",
        "max_tokens": 2048,
        "temperature": 0.7,
    }

    accepted_input_types = ["Text", "TextContent", "ChatMessage"]
    produced_output_types = ["Text", "TextContent", "ChatMessage"]

    text_output_field = "text"

    input_schema = Schema(
        content_type=ContentType.TEXT,
        required_fields=[],
        optional_fields=["text", "message", "context"],
        format_hints={"max_length": 100000},
    )

    output_schema = Schema(
        content_type=ContentType.TEXT,
        required_fields=["text"],
        optional_fields=["provider", "model", "tokens", "status"],
        format_hints={},
    )

    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Ask anything...",
            "multiline": True,
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "text", "type": "markdown", "label": "Response"},
            ],
        },
        "quick_actions": [
            {"icon": "💡", "label": "Explain", "prompt": "Explain this in simple terms"},
            {"icon": "📝", "label": "Summarize", "prompt": "Summarize the key points"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        if isinstance(input_data, dict):
            message = (
                input_data.get("text")
                or input_data.get("content")
                or input_data.get("extracted_text")
                or str(input_data)
            )
        else:
            message = str(input_data)

        max_tokens = params.get("max_tokens", self.config.get("max_tokens", 2048))
        temperature = params.get("temperature", self.config.get("temperature", 0.7))
        stream = params.get("stream", False)
        model = params.get("model", "deepseek-chat")

        system_prompt_text = self._resolve_system_prompt(input_data, params)

        use_rag = bool(
            params.get("use_rag")
            or (isinstance(input_data, dict) and input_data.get("use_rag"))
        )
        rag_project_id = (
            params.get("project_id")
            or (isinstance(input_data, dict) and input_data.get("project_id"))
        )
        if use_rag and rag_project_id:
            try:
                from app.core.rag.retriever import retrieve as _retrieve
                rag_k = int(params.get("rag_k", 5))
                chunks = _retrieve(message, str(rag_project_id), k=rag_k)
                if chunks:
                    context = "\n\n".join(
                        f"[{c.doc_id}#{c.chunk_index}] {c.text}" for c in chunks
                    )
                    message = (
                        f"Relevant project context:\n{context}\n\n"
                        f"---\n\nUser question: {message}"
                    )
            except Exception as exc:  # noqa: BLE001
                _logging = logging.getLogger(__name__)
                _logging.warning(
                    "RAG retrieval failed for project %s: %s", rag_project_id, exc
                )

        use_local_model = bool(
            params.get("use_local_model")
            or (isinstance(input_data, dict) and input_data.get("use_local_model"))
        )
        if use_local_model:
            try:
                from app.core.learning import local_model as _local
            except ImportError:
                _local = None  # type: ignore

            if _local is not None and _local.available():
                local_text = _local.generate(
                    message,
                    max_new_tokens=int(max_tokens),
                    temperature=float(temperature),
                )
                if local_text:
                    return {
                        "status": "success",
                        "response": local_text,
                        "provider": "local_lora",
                        "model": os.getenv("LOCAL_BASE_MODEL") or "Qwen/Qwen2.5-3B-Instruct",
                        "adapter": os.getenv("LOCAL_ADAPTER_DIR") or "data/learning/adapters/default",
                    }
                logging.getLogger(__name__).info(
                    "use_local_model requested but generate() returned None; falling back to cloud"
                )
            else:
                logging.getLogger(__name__).info(
                    "use_local_model requested but local stack unavailable; falling back to cloud"
                )

        from app.core.llm_config import _llm_config  # local import: avoid cycle at module load
        cfg = _llm_config()
        primary_error = None

        api_key = os.getenv(cfg["env_key"]) if cfg["env_key"] else ""
        if cfg["provider"] == "ollama" or (cfg["env_key"] and api_key):
            effective_model = model
            if cfg["provider"] != "deepseek" and effective_model.startswith("deepseek-"):
                effective_model = cfg["default_model"]
            extra_kwargs = {"system_prompt": system_prompt_text} if system_prompt_text else {}
            result = await self._call_cloud(
                message, effective_model, max_tokens, temperature, stream,
                api_key, cfg,
                **extra_kwargs,
            )
            if result.get("status") == "success":
                return result
            primary_error = result.get("error", f"{cfg['provider']} call failed")
        else:
            primary_error = f"{cfg['env_key']} not configured"

        local = await self._call_local(
            message, max_tokens, temperature, primary_error,
            system_prompt=system_prompt_text,
        )
        if local.get("status") == "success":
            return local

        return self._offline_template(message, primary_error, local.get("error"))

    @staticmethod
    def _build_messages(message: str, system_prompt: Optional[str]) -> list:
        msgs = []
        if system_prompt and system_prompt.strip():
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": message})
        return msgs

    def _resolve_system_prompt(
        self, input_data: Any, params: Dict
    ) -> Optional[str]:
        literal = None
        if isinstance(input_data, dict):
            literal = input_data.get("system_prompt")
        if not literal:
            literal = params.get("system_prompt")
        if isinstance(literal, str) and literal.strip():
            return literal

        fname = None
        if isinstance(input_data, dict):
            fname = input_data.get("system_prompt_file")
        if not fname:
            fname = params.get("system_prompt_file")
        if not fname:
            return None
        if not isinstance(fname, str):
            return None

        log = logging.getLogger(__name__)
        prompts_dir = (Path(__file__).parent.parent / "prompts").resolve()
        try:
            candidate = (prompts_dir / fname).resolve()
        except (OSError, ValueError) as exc:
            log.warning("system_prompt_file %r could not be resolved: %s", fname, exc)
            return None

        try:
            inside = candidate.is_relative_to(prompts_dir)
        except AttributeError:
            inside = str(candidate).startswith(str(prompts_dir) + os.sep)
        if not inside or candidate == prompts_dir:
            log.warning(
                "system_prompt_file %r rejected — resolves outside app/prompts/",
                fname,
            )
            return None
        if not candidate.is_file():
            log.warning(
                "system_prompt_file %r not found at %s", fname, candidate,
            )
            return None
        try:
            return candidate.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning(
                "system_prompt_file %r failed to read: %s", fname, exc,
            )
            return None

    async def _call_cloud(
        self,
        message: str,
        model: str,
        max_tokens: int,
        temperature: float,
        stream: bool,
        api_key: str,
        cfg: Dict[str, str],
        system_prompt: Optional[str] = None,
    ) -> Dict:
        url = cfg["url"]
        provider_name = cfg["provider"]
        messages = self._build_messages(message, system_prompt)
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        if stream:
            async def _stream_generator():
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        url,
                        headers=headers,
                        json={
                            "model": model,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "stream": True,
                        },
                    ) as response:
                        if response.status_code != 200:
                            err = await response.aread()
                            yield json.dumps({
                                "type": "error",
                                "message": f"{provider_name} error {response.status_code}: {err[:200]}",
                            })
                            return
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue

            return {
                "status": "success",
                "text": "",
                "provider": provider_name,
                "model": model,
                "stream": _stream_generator(),
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "error": f"{provider_name} API error (HTTP {response.status_code}): {response.text[:200]}",
                    }
                data = response.json()
                return {
                    "status": "success",
                    "text": data["choices"][0]["message"]["content"],
                    "provider": provider_name,
                    "model": model,
                    "tokens": data.get("usage", {}),
                }
        except httpx.TimeoutException:
            return {"status": "error", "error": f"{provider_name} request timed out"}
        except Exception as e:
            return {"status": "error", "error": f"{provider_name} failed: {e}"}

    async def _call_local(
        self,
        message: str,
        max_tokens: int,
        temperature: float,
        primary_error: str,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        ollama_url = os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL)
        local_model = os.getenv("LOCAL_LLM_MODEL", DEFAULT_LOCAL_MODEL)
        ollama_result = await self._call_ollama(
            message, local_model, max_tokens, temperature, ollama_url,
            system_prompt=system_prompt,
        )
        if ollama_result.get("status") == "success":
            ollama_result["fallback_reason"] = primary_error
            return ollama_result

        gguf_path = os.getenv("LLAMA_CPP_MODEL_PATH")
        if gguf_path and os.path.exists(gguf_path):
            llama_result = self._call_llama_cpp(
                message, gguf_path, max_tokens, temperature,
                system_prompt=system_prompt,
            )
            if llama_result.get("status") == "success":
                llama_result["fallback_reason"] = primary_error
                return llama_result
            return {
                "status": "error",
                "error": f"ollama: {ollama_result.get('error')}; llama_cpp: {llama_result.get('error')}",
            }

        return {
            "status": "error",
            "error": f"ollama unavailable ({ollama_result.get('error')}); no LLAMA_CPP_MODEL_PATH set",
        }

    async def _call_ollama(
        self,
        message: str,
        model: str,
        max_tokens: int,
        temperature: float,
        base_url: str,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        try:
            messages = self._build_messages(message, system_prompt)
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                        "stream": False,
                    },
                )
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "error": f"ollama HTTP {response.status_code}: {response.text[:200]}",
                    }
                data = response.json()
                text = (data.get("message") or {}).get("content", "")
                if not text:
                    return {"status": "error", "error": "ollama returned empty content"}
                return {
                    "status": "success",
                    "text": text,
                    "provider": "local_ollama",
                    "model": model,
                    "tokens": {
                        "input_tokens": data.get("prompt_eval_count"),
                        "output_tokens": data.get("eval_count"),
                    },
                }
        except httpx.ConnectError:
            return {"status": "error", "error": f"ollama not reachable at {base_url}"}
        except httpx.TimeoutException:
            return {"status": "error", "error": "ollama request timed out"}
        except Exception as e:
            return {"status": "error", "error": f"ollama failed: {e}"}

    def _call_llama_cpp(
        self,
        message: str,
        gguf_path: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        try:
            from llama_cpp import Llama  # type: ignore
        except Exception as e:
            return {"status": "error", "error": f"llama-cpp-python not importable: {e}"}

        try:
            llm = Llama(model_path=gguf_path, n_ctx=4096, verbose=False)
            messages = self._build_messages(message, system_prompt)
            out = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = (out.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if not text:
                return {"status": "error", "error": "llama.cpp returned empty content"}
            return {
                "status": "success",
                "text": text,
                "provider": "local_llama_cpp",
                "model": os.path.basename(gguf_path),
                "tokens": out.get("usage", {}),
            }
        except Exception as e:
            return {"status": "error", "error": f"llama.cpp failed: {e}"}

    def _offline_template(self, message: str, primary_error: str, local_error: str) -> Dict:
        snippet = (message or "").strip()
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."
        body = (
            "**Chat is running in offline mode.**\n\n"
            "No cloud or local language model is currently reachable, so I can't "
            "generate an AI response right now. Your message was received intact:\n\n"
            f"> {snippet or '(empty)'}\n\n"
            "**How to restore full chat:**\n"
            "- Set `QWEN_API_KEY` (DashScope) in `.env` to use Qwen, **or**\n"
            "- Set `GROQ_API_KEY` (free tier) or `DEEPSEEK_API_KEY` to use another cloud provider, **or**\n"
            "- Run a local model: `ollama serve` + `ollama pull qwen2.5:3b-instruct`\n"
            "  (optionally set `OLLAMA_URL` and `LOCAL_LLM_MODEL`), **or**\n"
            "- Provide a GGUF file via `LLAMA_CPP_MODEL_PATH` with `llama-cpp-python` installed.\n\n"
            f"_Primary provider: {primary_error}_  \n"
            f"_Local inference: {local_error}_"
        )
        return {
            "status": "success",
            "text": body,
            "provider": "offline_template",
            "model": "template:v1",
            "primary_error": primary_error,
            "local_error": local_error,
        }
