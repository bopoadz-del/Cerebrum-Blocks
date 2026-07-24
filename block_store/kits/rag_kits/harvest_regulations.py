#!/usr/bin/env python3
"""
Harvest raw authoritative documents from the Regulations_Link_Retrieval.csv links.

For each regulation, this script:
  1. Fetches the linked URL.
  2. Detects PDF vs HTML.
  3. Extracts clean text (PDF via PyPDF2, HTML via lxml).
  4. Writes a .txt file and (for HTML) a raw .html fallback.
  5. Records a manifest with status, source, local path, and any errors.

Usage:
    python harvest_regulations.py
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any

import PyPDF2
import requests
from lxml import html

CSV_PATH = Path("Regulations_Link_Retrieval.csv")
OUT_DIR = Path("raw_regulations")
MANIFEST_PATH = OUT_DIR / "harvest_manifest.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_TIMEOUT = 60
SLEEP_SECONDS = 1.0
MAX_RETRIES = 2


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a regulation title."""
    base = name.strip().replace(" ", "_")
    base = re.sub(r"[^\w\-_.]", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base[:120] or "unnamed"


def detect_source(url: str) -> str:
    netloc = urllib.parse.urlparse(url).netloc.lower()
    if "eur-lex" in netloc:
        return "eur_lex"
    if "esma" in netloc:
        return "esma"
    if "ecfr" in netloc:
        return "ecfr"
    if "federalregister" in netloc:
        return "federal_register"
    if "fdic" in netloc:
        return "fdic"
    if "sec.gov" in netloc:
        return "sec"
    if "federalreserve" in netloc:
        return "federal_reserve"
    if "europa.eu" in netloc:
        return "europa_eu"
    return "other"


def extract_text_from_pdf(content: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            parts.append(txt)
    return "\n\n".join(parts)


def extract_text_from_html(content: bytes, url: str) -> str:
    tree = html.fromstring(content)
    # Drop noisy elements.
    for bad in tree.xpath(
        "//script|//style|//nav|//header|//footer|//aside|//noscript|//iframe"
    ):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    text = tree.text_content()
    # Collapse whitespace.
    lines = (line.strip() for line in text.splitlines())
    text = "\n".join(line for line in lines if line)
    return text


def fetch_url(url: str, retries: int = MAX_RETRIES) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise last_exc  # type: ignore[misc]


def harvest(row: dict[str, Any], idx: int) -> dict[str, Any]:
    law = row["Laws"].strip()
    url = row["Link"].strip()
    category = row["category"].strip()
    source = detect_source(url)

    safe_name = sanitize_filename(law)
    category_dir = OUT_DIR / sanitize_filename(category)
    category_dir.mkdir(parents=True, exist_ok=True)

    base_path = category_dir / f"{idx:03d}_{safe_name}"
    txt_path = base_path.with_suffix(".txt")
    html_path = base_path.with_suffix(".html")
    pdf_path = base_path.with_suffix(".pdf")

    result = {
        "index": idx,
        "law": law,
        "category": category,
        "source": source,
        "url": url,
        "txt_path": str(txt_path.relative_to(OUT_DIR)),
        "status": "pending",
        "error": None,
    }

    if not url:
        result["status"] = "skipped"
        result["error"] = "empty URL"
        return result

    # Resume: skip if we already harvested this entry in a previous run.
    if txt_path.exists() and txt_path.stat().st_size > 0:
        if pdf_path.exists():
            result["status"] = "ok_pdf"
        else:
            result["status"] = "ok_html"
        result["error"] = "resumed from existing files"
        return result

    try:
        resp = fetch_url(url)
        content_type = resp.headers.get("Content-Type", "").lower()
        is_pdf = (
            url.lower().endswith(".pdf")
            or "application/pdf" in content_type
            or resp.content[:4] == b"%PDF"
        )

        if is_pdf:
            pdf_path.write_bytes(resp.content)
            text = extract_text_from_pdf(resp.content)
            txt_path.write_text(text, encoding="utf-8")
            result["status"] = "ok_pdf"
        else:
            html_path.write_bytes(resp.content)
            text = extract_text_from_html(resp.content, url)
            txt_path.write_text(text, encoding="utf-8")
            result["status"] = "ok_html"

    except Exception as exc:
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    manifest: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=1):
        result = harvest(row, idx)
        manifest.append(result)
        print(
            f"[{idx}/{len(rows)}] {result['status']:10s} | "
            f"{result['category']:16s} | {result['law'][:60]}"
        )
        if result["error"]:
            print(f"         -> {result['error']}")
        time.sleep(SLEEP_SECONDS)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    ok = sum(1 for m in manifest if m["status"].startswith("ok"))
    err = sum(1 for m in manifest if m["status"] == "error")
    skipped = sum(1 for m in manifest if m["status"] == "skipped")
    print(f"\nHarvest complete: {ok} OK, {err} errors, {skipped} skipped.")
    print(f"Manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
