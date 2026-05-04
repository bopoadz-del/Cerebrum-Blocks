"""Capture Block — Any client pushes images, get structured data back.

Pipeline:
  Image → OCR (Tesseract ara+eng) → Raw Text → LLM Structuring → Vector DB
"""

import os
import io
import uuid
import json
import tempfile
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.universal_base import UniversalBlock
from app.core.typed_block import TypedBlock, Schema, ContentType


class CaptureBlock(TypedBlock):
    """Universal capture block: image → OCR → AI → structured data → vector store."""

    name = "capture"
    version = "1.0.0"
    description = "Receive images from any client, OCR extract, AI structure, vector store"
    layer = 3
    tags = ["capture", "ocr", "vision", "ai", "multimodal", "knowledge"]
    requires = ["vector_search"]

    input_schema = Schema(
        content_type=ContentType.IMAGE,
        required_fields=["image"],
        optional_fields=["file_path", "bytes", "base64", "source", "user_id", "capture_id"],
        format_hints={"accept": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]}
    )

    output_schema = Schema(
        content_type=ContentType.JSON,
        required_fields=["capture_id", "status", "raw_text", "clean_text", "summary"],
        optional_fields=["entities", "tags", "language_detected", "ocr_confidence", "ocr_engine", "memory_id"],
        format_hints={}
    )

    accepted_input_types = ["Image", "ImageContent", "File"]
    produced_output_types = ["Text", "JSON", "CaptureResult"]


    async def execute(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        action = params.get("action") if isinstance(params, dict) else None
        if isinstance(input_data, str):
            if action == "structure":
                input_data = {"text": input_data}
            else:
                input_data = {"image": input_data}
        return await super().execute(input_data, params)

    def validate_input(self, data: Any) -> Dict[str, Any]:
        if isinstance(data, dict) and data.get("action") in {"health", "status", "list", "history", "get", "unschedule", "broadcast", "search", "summarize", "structure", "execute_async", "ocr"}:
            return {"valid": True, "errors": [], "warnings": [], "data": data}
        return super().validate_input(data)

    default_config = {
        "ocr_languages": "ara+eng",
        "ocr_engine": "tesseract",
        "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        "vector_db_url": os.getenv("VECTOR_DB_URL", "http://localhost:8001"),
        "store_captures": True,
        "capture_collection": "cerebrum_captures",
    }

    ui_schema = {
        "input": {
            "type": "image",
            "accept": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"],
            "placeholder": "Upload or push an image to capture and structure...",
            "multiline": False,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "capture_id", "type": "text", "label": "Capture ID"},
                {"name": "raw_text", "type": "text", "label": "OCR Raw Text"},
                {"name": "entities", "type": "json", "label": "Entities"},
                {"name": "tags", "type": "array", "label": "Tags"},
                {"name": "summary", "type": "text", "label": "Summary"},
                {"name": "clean_text", "type": "text", "label": "Clean Text"},
            ],
        },
        "quick_actions": [
            {"icon": "📸", "label": "Capture Image", "prompt": "Capture and structure this image"},
            {"icon": "🔍", "label": "OCR Only", "prompt": "Extract raw text only"},
            {"icon": "🧠", "label": "AI Structure", "prompt": "Structure captured text into entities and summary"},
        ],
    }


    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self._ensure_dirs()

    def _ensure_dirs(self):
        d = os.getenv("DATA_DIR", "./data")
        self.capture_dir = os.path.join(d, "captures")
        os.makedirs(self.capture_dir, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Main entry: accepts image path, bytes, or dict with file info."""
        params = params or {}
        action = params.get("action", "capture")

        if action == "capture":
            return await self._capture(input_data, params)
        elif action == "ocr":
            return await self._ocr_only(input_data, params)
        elif action == "structure":
            return await self._structure_text(input_data, params)
        elif action == "search":
            return await self._search_captures(input_data, params)
        else:
            return {"status": "error", "error": f"Unknown action: {action}"}

    async def _capture(self, input_data: Any, params: Dict) -> Dict:
        """Full pipeline: image → vision/OCR → structure → store."""
        # 1. Resolve image
        image_path = await self._resolve_image(input_data)
        if not image_path or not os.path.exists(image_path):
            return {"status": "error", "error": "No valid image provided"}

        capture_id = params.get("capture_id") or self._generate_id()
        source = params.get("source", "unknown")
        user_id = params.get("user_id", "anonymous")

        # Prefer Claude Vision when API key is available
        anthropic_key = self.config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            vision_result = await self._vision_with_claude(image_path, params)
            if vision_result.get("status") == "error":
                return vision_result
            result = {
                "status": "success",
                "capture_id": capture_id,
                "source": source,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_text": vision_result.get("raw_text", ""),
                "clean_text": vision_result.get("clean_text", ""),
                "entities": vision_result.get("entities", []),
                "tags": vision_result.get("tags", []),
                "summary": vision_result.get("summary", ""),
                "language_detected": vision_result.get("language", "unknown"),
                "ocr_engine": "claude-vision",
                "ocr_confidence": vision_result.get("confidence", 0.95),
                "image_path": image_path,
            }
        else:
            # 2. OCR
            ocr_result = await self._run_ocr(image_path, params)
            if ocr_result.get("status") == "error":
                return ocr_result
            raw_text = ocr_result.get("text", "")

            # 3. LLM structuring
            structured = await self._structure_with_llm(raw_text, params)

            # 4. Build result
            result = {
                "status": "success",
                "capture_id": capture_id,
                "source": source,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_text": raw_text,
                "clean_text": structured.get("clean_text", raw_text),
                "entities": structured.get("entities", []),
                "tags": structured.get("tags", []),
                "summary": structured.get("summary", ""),
                "language_detected": structured.get("language", "unknown"),
                "ocr_engine": ocr_result.get("engine", "unknown"),
                "ocr_confidence": ocr_result.get("confidence", 0),
                "image_path": image_path,
            }

        # 5. Vector store
        if self.config.get("store_captures", True):
            stored_id = await self._store_in_vector_db(capture_id, result)
            result["memory_id"] = stored_id

        return result

    async def _ocr_only(self, input_data: Any, params: Dict) -> Dict:
        image_path = await self._resolve_image(input_data)
        if not image_path or not os.path.exists(image_path):
            return {"status": "error", "error": "No valid image provided"}
        return await self._run_ocr(image_path, params)

    async def _structure_text(self, input_data: Any, params: Dict) -> Dict:
        text = input_data if isinstance(input_data, str) else str(input_data)
        structured = await self._structure_with_llm(text, params)
        return {"status": "success", **structured}

    async def _search_captures(self, input_data: Any, params: Dict) -> Dict:
        query = input_data if isinstance(input_data, str) else str(input_data)
        return await self._search_vectors(query, params)

    # ── Image resolution ───────────────────────────────────────────────────────

    async def _resolve_image(self, input_data: Any) -> Optional[str]:
        """Turn input into a local file path."""
        if isinstance(input_data, str):
            if os.path.exists(input_data):
                return input_data
            # Check if it looks like a file path (has extension or starts with /)
            looks_like_path = input_data.startswith("/") or "." in os.path.basename(input_data)
            if looks_like_path:
                raise ValueError(f"File not found: {input_data}")
            # Assume base64
            return self._save_base64(input_data)
        elif isinstance(input_data, bytes):
            return self._save_bytes(input_data)
        elif isinstance(input_data, dict):
            if input_data.get("file_path"):
                path = input_data["file_path"]
                if os.path.exists(path):
                    return path
                raise ValueError(f"File not found: {path}")
            if input_data.get("bytes"):
                return self._save_bytes(input_data["bytes"])
            if input_data.get("base64"):
                return self._save_base64(input_data["base64"])
            if input_data.get("image"):
                img = input_data["image"]
                if isinstance(img, str):
                    if os.path.exists(img):
                        return img
                    # Check if it looks like a file path
                    looks_like_path = img.startswith("/") or "." in os.path.basename(img)
                    if looks_like_path:
                        raise ValueError(f"File not found: {img}")
                    return self._save_base64(img)
                elif isinstance(img, bytes):
                    return self._save_bytes(img)
        return None

    def _save_bytes(self, data: bytes, ext: str = ".png") -> str:
        fid = self._generate_id()
        path = os.path.join(self.capture_dir, f"{fid}{ext}")
        with open(path, "wb") as f:
            f.write(data)
        return path

    def _save_base64(self, b64data: str, ext: str = ".png") -> str:
        import base64
        # Strip data URI prefix if present
        if "," in b64data:
            b64data = b64data.split(",", 1)[1]
        raw = base64.b64decode(b64data)
        return self._save_bytes(raw, ext)

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    # ── OCR ────────────────────────────────────────────────────────────────────

    async def _run_ocr(self, image_path: str, params: Dict) -> Dict:
        languages = params.get("languages", self.config.get("ocr_languages", "ara+eng"))
        engine = self.config.get("ocr_engine", "tesseract")

        if engine == "tesseract":
            return await self._ocr_tesseract(image_path, languages)
        else:
            return await self._ocr_easyocr(image_path, languages.split("+") if "+" in languages else [languages])

    async def _ocr_tesseract(self, image_path: str, languages: str) -> Dict:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Preprocess for better OCR
            gray = img.convert("L")

            text = pytesseract.image_to_string(gray, lang=languages)
            data = pytesseract.image_to_data(gray, lang=languages, output_type=pytesseract.Output.DICT)

            confs = [int(c) for c in data["conf"] if int(c) > 0]
            avg_conf = sum(confs) / len(confs) if confs else 0

            return {
                "status": "success",
                "text": text.strip(),
                "confidence": round(avg_conf / 100, 2),  # Tesseract confidence 0-100
                "engine": "tesseract",
                "languages": languages,
                "word_count": len(text.split()),
            }
        except ImportError:
            return {"status": "error", "error": "pytesseract not installed. Run: pip install pytesseract pillow"}
        except Exception as e:
            return {"status": "error", "error": f"Tesseract OCR failed: {str(e)}"}

    async def _ocr_easyocr(self, image_path: str, languages: List[str]) -> Dict:
        try:
            import easyocr
            reader = easyocr.Reader(languages, gpu=False)
            results = reader.readtext(image_path)

            if not results:
                return {"status": "success", "text": "", "confidence": 0, "engine": "easyocr"}

            texts = [r[1] for r in results if r[1].strip()]
            confs = [r[2] for r in results]
            full_text = "\n".join(texts)
            avg_conf = sum(confs) / len(confs) if confs else 0

            return {
                "status": "success",
                "text": full_text,
                "confidence": round(avg_conf, 2),
                "engine": "easyocr",
                "languages": languages,
                "word_count": len(full_text.split()),
            }
        except ImportError:
            return {"status": "error", "error": "easyocr not installed"}
        except Exception as e:
            return {"status": "error", "error": f"EasyOCR failed: {str(e)}"}

    # ── Vision (Claude) ────────────────────────────────────────────────────────

    async def _vision_with_claude(self, image_path: str, params: Dict) -> Dict:
        import base64
        import httpx

        api_key = self.config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return {"status": "error", "error": "Anthropic API key not configured"}

        model = self.config.get("anthropic_model", "claude-3-5-sonnet-20241022")

        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            return {"status": "error", "error": f"Failed to read image: {str(e)}"}

        ext = os.path.splitext(image_path)[1].lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        system_prompt = (
            "You are a structured data extraction engine. "
            "Analyze the provided image and output ONLY valid JSON. "
            "No markdown, no explanation, just JSON."
        )
        user_prompt = (
            "Describe the image in detail and extract structured data. "
            "Return JSON with exactly these keys:\n"
            "- raw_text: any text visible in the image (OCR result)\n"
            "- clean_text: cleaned, properly formatted text\n"
            "- summary: one-sentence summary of the image content\n"
            "- entities: list of {\"type\": \"person|org|location|date|amount|other\", \"value\": \"...\"}\n"
            "- tags: list of relevant keywords (5-10 tags)\n"
            "- language: detected primary language (ar, en, mixed)\n"
            "- confidence: estimated confidence 0-1"
        )

        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get("content", [])
                text_content = ""
                for block in content:
                    if block.get("type") == "text":
                        text_content += block.get("text", "")
                parsed = self._safe_parse_json(text_content)
                return {
                    "status": "success",
                    "raw_text": parsed.get("raw_text", text_content),
                    "clean_text": parsed.get("clean_text", text_content),
                    "summary": parsed.get("summary", ""),
                    "entities": parsed.get("entities", []),
                    "tags": parsed.get("tags", []),
                    "language": parsed.get("language", "unknown"),
                    "confidence": parsed.get("confidence", 0.95),
                }
        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"Claude Vision API error: {e.response.status_code} {e.response.text}"}
        except Exception as e:
            return {"status": "error", "error": f"Claude Vision failed: {str(e)}"}

    # ── LLM Structuring ────────────────────────────────────────────────────────

    async def _structure_with_llm(self, raw_text: str, params: Dict) -> Dict:
        """Send raw OCR text to LLM for entity extraction, tagging, summarization."""
        provider = params.get("llm_provider", self.config.get("llm_provider", "deepseek"))
        max_chars = params.get("max_chars", 4000)
        truncated = raw_text[:max_chars]

        system_prompt = (
            "You are a structured data extraction engine. "
            "Take raw OCR text (possibly Arabic + English mixed) and output ONLY valid JSON. "
            "No markdown, no explanation, just JSON."
        )
        user_prompt = f"""Extract from the following OCR text:

---
{truncated}
---

Return JSON with exactly these keys:
- clean_text: cleaned, properly formatted text
- summary: one-sentence summary
- entities: list of {{"type": "person|org|location|date|amount|other", "value": "..."}}
- tags: list of relevant keywords (5-10 tags)
- language: detected primary language (ar, en, mixed)
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self._llm_chat(messages, provider)
            content = response.get("content", "{}")
            parsed = self._safe_parse_json(content)
            return parsed
        except Exception as e:
            # Fallback: return raw text as clean_text
            return {
                "clean_text": raw_text,
                "summary": "",
                "entities": [],
                "tags": [],
                "language": "unknown",
                "error": str(e),
            }

    async def _llm_chat(self, messages: List[Dict], provider: str) -> Dict:
        import httpx

        if provider == "ollama":
            url = f"{self.config.get('ollama_base_url')}/api/chat"
            payload = {
                "model": self.config.get("ollama_model", "llama3.2:3b"),
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "content": data["message"]["content"],
                    "model": self.config.get("ollama_model"),
                    "provider": "ollama",
                }

        elif provider == "deepseek":
            api_key = self.config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                return {"status": "error", "error": "DeepSeek API key not configured"}
            model = self.config.get("deepseek_model", "deepseek-chat")
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": model,
                    "provider": "deepseek",
                    "tokens": data.get("usage", {}).get("total_tokens", 0),
                }

        elif provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.get('openrouter_api_key')}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.config.get("openrouter_model", "anthropic/claude-3.5-sonnet"),
                "messages": messages,
                "temperature": 0.2,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": self.config.get("openrouter_model"),
                    "provider": "openrouter",
                }

            return {"status": "error", "error": "Vector DB not configured"}
        try:
            payload = {"collection": collection, "query": query, "n_results": n_results}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{db_url}/api/v1/collections/query", json=payload)
                if resp.status_code == 200:
                    return {"status": "success", "results": resp.json().get("results", [])}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "error", "error": "Search failed"}
