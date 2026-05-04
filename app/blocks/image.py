"""Image Block - Claude Vision analysis + Stability AI image generation + PIL metadata"""

import base64
import io
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict

import httpx
from PIL import Image

from app.core.universal_base import UniversalBlock

_MODEL = "claude-sonnet-4-5-20251001"
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _load_image_b64(file_path: str) -> tuple[str, str]:
    """Return (base64_data, media_type) for a local file."""
    mime, _ = mimetypes.guess_type(file_path)
    media_type = mime or "image/jpeg"
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


async def _download_image_b64(url: str) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    data = base64.standard_b64encode(resp.content).decode("utf-8")
    return data, content_type


async def _analyze_with_claude(img_data: str, media_type: str, prompt: str, api_key: str) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    msg = await client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return msg.content[0].text


async def _generate_with_stability(prompt: str, api_key: str, width: int = 1024, height: int = 1024) -> bytes:
    """Generate an image using Stability AI and return raw PNG bytes."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
            files={"none": ("", "")},
            data={
                "prompt": prompt,
                "output_format": "png",
                "width": width,
                "height": height,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(f"Stability AI error {response.status_code}: {response.text[:500]}")
        return response.content


def _pil_metadata(file_path: str) -> Dict:
    img = Image.open(file_path)
    width, height = img.size
    mode = img.mode
    fmt = img.format or Path(file_path).suffix.upper().lstrip(".")
    file_size = os.path.getsize(file_path)

    info = {
        "width": width,
        "height": height,
        "mode": mode,
        "format": fmt,
        "file_size_bytes": file_size,
        "megapixels": round(width * height / 1_000_000, 2),
        "aspect_ratio": f"{width}:{height}",
    }

    if mode in ("RGB", "RGBA"):
        r, g, b = img.convert("RGB").split()
        info["dominant_channel"] = max(
            ("red", _avg(r)), ("green", _avg(g)), ("blue", _avg(b)),
            key=lambda x: x[1],
        )[0]

    return info


def _avg(channel) -> float:
    import numpy as np
    return float(np.array(channel).mean())


class ImageBlock(UniversalBlock):
    """Image analysis via Claude Vision; generation via Stability AI; PIL metadata fallback."""

    name = "image"
    version = "2.0"
    description = "Analyze images with Claude Vision AI, generate images with Stability AI, or extract basic metadata"
    layer = 3
    tags = ["domain", "vision", "image"]
    requires = []

    ui_schema = {
        "input": {
            "type": "image",
            "accept": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
            "placeholder": "Upload image to analyze...",
            "multiline": True,
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "description", "type": "markdown", "label": "Analysis"},
                {"name": "objects_detected", "type": "array", "label": "Objects"},
            ],
        },
        "quick_actions": [
            {"icon": "🖼️", "label": "Analyze Image", "prompt": "Describe what's in this image"},
            {"icon": "📐", "label": "Construction", "prompt": "Analyze this construction drawing"},
            {"icon": "🔍", "label": "Extract Text", "prompt": "Extract all text from this image"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        operation = params.get("operation", "analyze")
        prompt = params.get("prompt", "Describe this image in detail. List any key objects, text, or notable features.")

        # Resolve source
        file_path = None
        url = None
        if isinstance(input_data, str):
            if input_data.startswith("http"):
                url = input_data
            elif os.path.exists(input_data):
                file_path = input_data
            else:
                return {
                    "status": "success",
                    "mode": "demo",
                    "note": "No valid image file or URL provided. Below is demo image analysis output.",
                    "description": "Demo: Site photo showing concrete foundation pour with rebar reinforcement. Workers in PPE visible. Formwork appears aligned.",
                    "objects": ["concrete", "rebar", "formwork", "workers", "ppe"],
                    "confidence": 0.78,
                }
        elif isinstance(input_data, dict):
            file_path = input_data.get("file_path") or input_data.get("path")
            url = input_data.get("url")
            prompt = input_data.get("prompt", prompt)
            if not file_path and not url:
                raw = input_data.get("text") or input_data.get("input") or ""
                if raw.startswith("http"):
                    url = raw
                elif raw and os.path.exists(raw):
                    file_path = raw
        elif input_data is None and operation == "generate":
            pass
        else:
            return {"status": "error", "error": "Input must be a file path, URL, or {file_path, url, prompt}"}

        if operation == "metadata":
            try:
                if url and not file_path:
                    import tempfile
                    img_data, media_type = await _download_image_b64(url)
                    raw = base64.b64decode(img_data)
                    suffix = "." + media_type.split("/")[-1].split(";")[0]
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                        f.write(raw)
                        tmp = f.name
                    try:
                        meta = _pil_metadata(tmp)
                    finally:
                        try:
                            os.unlink(tmp)
                        except OSError:
                            pass
                elif file_path:
                    meta = _pil_metadata(file_path)
                else:
                    return {"status": "error", "error": "Provide file_path or url for metadata"}
                return {"status": "success", "operation": "metadata", **meta}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        if operation == "generate":
            stability_key = os.getenv("STABILITY_API_KEY")
            if not stability_key:
                return {
                    "status": "error",
                    "error": "STABILITY_API_KEY not set. Set it to enable AI image generation.",
                }
            try:
                if not prompt or prompt == "Describe this image in detail. List any key objects, text, or notable features.":
                    prompt = input_data if isinstance(input_data, str) else "A beautiful landscape"
                width = params.get("width", 1024)
                height = params.get("height", 1024)
                image_bytes = await _generate_with_stability(prompt, stability_key, width, height)
                return {
                    "status": "success",
                    "operation": "generate",
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
                    "format": "png",
                    "provider": "stability",
                }
            except Exception as e:
                return {"status": "error", "error": f"Image generation failed: {str(e)}", "operation": "generate"}

        # Analyze operation
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            return {
                "status": "success",
                "mode": "demo",
                "note": "ANTHROPIC_API_KEY not set. Below is demo image analysis output.",
                "description": "Demo: Site photo showing concrete foundation pour with rebar reinforcement. Workers in PPE visible. Formwork appears aligned.",
                "objects": ["concrete", "rebar", "formwork", "workers", "ppe"],
                "confidence": 0.78,
            }

        try:
            if url:
                img_data, media_type = await _download_image_b64(url)
            elif file_path:
                img_data, media_type = _load_image_b64(file_path)
            else:
                return {"status": "error", "error": "Provide file_path or url for analysis"}

            if len(img_data) * 3 // 4 > _MAX_IMAGE_BYTES:
                return {"status": "error", "error": "Image too large (max 5 MB)"}

            if operation == "extract_text":
                prompt = "Extract all visible text from this image exactly as it appears. Format clearly."
            elif operation == "construction":
                prompt = (
                    "Analyze this construction drawing or site photo. Identify: "
                    "document type, scale/dimensions if visible, materials mentioned, "
                    "key measurements, any annotations, and overall purpose."
                )

            description = await _analyze_with_claude(img_data, media_type, prompt, anthropic_key)

            result = {
                "status": "success",
                "operation": operation,
                "description": description,
                "model": _MODEL,
                "source": url or (os.path.basename(file_path) if file_path else ""),
            }

            if file_path:
                try:
                    meta = _pil_metadata(file_path)
                    result["metadata"] = meta
                except Exception:
                    pass

            return result

        except Exception as e:
            return {"status": "error", "error": str(e), "operation": operation}
