"""OCRBlock.process — entry-point coverage, and the wall it runs into.

Why this file exists
--------------------
``tests/blocks/test_ocr.py`` drives ``execute`` and asserts only the
UniversalBlock envelope keys, so the control-delete in
``scripts/certify_block.py`` gutted ``OCRBlock.process`` and that suite stayed
GREEN.

What this file found
--------------------
``OCRBlock.process`` cannot reach a real artifact in this Store *at all*. For
any input that resolves to an existing file it calls ``_process_image``, whose
first statement is ``_detect_markup``, whose first statement is

    from app.core.redline import detect_redlines, summarize_markup

— an unconditional import, outside the function's ``try``. ``app.core.redline``
does not exist in this repository, and neither does ``app.core.image_quality``
(imported a few lines later for ``summarize_ocr_quality``). So every image and
every PDF raises ``ModuleNotFoundError`` before a single pixel is read, and
``UniversalBlock.execute`` swallows it into a generic error envelope — which is
exactly why the block looked certifiable.

The registry's earlier note blamed a missing OCR fixture. The fixture is not
the blocker: ``tests/fixtures/drawing_tm_1100010.pdf`` is a real 485 KB
construction drawing, and the two tests at the bottom of this file drive it
straight into the missing import.

``test_real_drawing_cannot_be_read_*`` are defect pins, not a specification.
When ``app.core.redline`` and ``app.core.image_quality`` land, they will fail
loudly and must be replaced with assertions on extracted text.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.blocks.ocr import OCRBlock


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DRAWING = FIXTURES / "drawing_tm_1100010.pdf"


# ── the paths that do return a payload ─────────────────────────────────────


async def test_missing_file_reports_the_path_it_was_given():
    result = await OCRBlock().process({"file_path": "/tmp/no_such_scan.png"}, {})

    assert result["status"] == "error"
    assert result["error"] == "File not found: /tmp/no_such_scan.png"
    assert result["text"] == ""
    assert result["confidence"] == 0


async def test_bare_string_path_is_resolved_and_reported_by_name():
    """A bare string is treated as a path, not as prompt text."""
    result = await OCRBlock().process("/tmp/also_missing.tiff", {})

    assert result["status"] == "error"
    assert result["error"] == "File not found: /tmp/also_missing.tiff"


async def test_input_carrying_no_path_is_rejected_by_name():
    result = await OCRBlock().process({"language": "eng"}, {})

    assert result["status"] == "error"
    assert result["error"] == "No image provided"
    assert result["text"] == ""
    assert result["confidence"] == 0


async def test_a_pil_image_object_is_not_a_path_and_is_refused():
    """The block only accepts paths; an in-memory image is not one.

    tests/blocks/test_ocr.py passes ``{"image": <PIL.Image>}`` and asserts the
    envelope, which hides the fact that the block never looks at it.
    """
    from PIL import Image

    result = await OCRBlock().process({"image": Image.new("RGB", (40, 20))}, {})

    assert result["status"] == "error"
    assert result["error"] == "No image provided"


# ── the path that cannot return a payload (defect pins) ────────────────────


async def test_real_drawing_cannot_be_read_missing_app_core_redline():
    """A real PDF on disk raises before any page is rasterised."""
    assert DRAWING.is_file()

    with pytest.raises(ModuleNotFoundError, match=r"app\.core\.redline"):
        await OCRBlock().process({"file_path": str(DRAWING)}, {})


async def test_execute_masks_that_crash_as_a_generic_error_envelope():
    """Why the block certified clean before: execute() catches it."""
    envelope = await OCRBlock().execute({"file_path": str(DRAWING)}, {})

    assert envelope["block"] == "ocr"
    assert envelope["status"] == "error"
    assert "app.core.redline" in envelope["result"]["error"]
