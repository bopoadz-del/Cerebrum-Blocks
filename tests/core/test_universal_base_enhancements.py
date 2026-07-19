"""Tests for the Fork-derived enhancements to UniversalBlock."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from app.core.universal_base import UniversalBlock


class RequiredFieldBlock(UniversalBlock):
    name = "required_field_block"
    version = "1.0.0"
    required_input_fields = ["file_path"]

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        return {"status": "success", "received": input_data}


class OneOfBlock(UniversalBlock):
    name = "one_of_block"
    version = "1.0.0"
    required_input_one_of = ["text", "file_path"]

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        return {"status": "success", "received": input_data}


class SkipActionBlock(UniversalBlock):
    name = "skip_action_block"
    version = "1.0.0"
    required_input_fields = ["file_path"]
    skip_input_validation_actions = ["status", "health"]

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        return {"status": "success", "received": input_data}


class EmptyInputBlock(UniversalBlock):
    name = "empty_input_block"
    version = "1.0.0"
    required_input_fields = ["file_path"]
    allow_empty_input = True

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        return {"status": "success", "received": input_data}


class TextOutputFieldBlock(UniversalBlock):
    name = "text_output_field_block"
    version = "1.0.0"
    text_output_field = "translated"

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        return {"status": "success", "translated": "bonjour"}


class AutoValidateOffBlock(UniversalBlock):
    name = "auto_validate_off_block"
    version = "1.0.0"
    auto_validate = False

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        return {"status": "success", "text": "hello"}


@pytest.mark.asyncio
async def test_required_field_enforced():
    block = RequiredFieldBlock()
    result = await block.execute({})
    assert result["status"] == "error"
    assert "Missing required field" in str(result["result"])


@pytest.mark.asyncio
async def test_required_field_in_params_satisfies():
    block = RequiredFieldBlock()
    result = await block.execute({}, params={"file_path": "/tmp/x.pdf"})
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_one_of_required():
    block = OneOfBlock()
    result = await block.execute({})
    assert result["status"] == "error"
    assert "At least one of" in str(result["result"])


@pytest.mark.asyncio
async def test_one_of_satisfied_by_text():
    block = OneOfBlock()
    result = await block.execute({"text": "hello"})
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_skip_validation_for_action():
    block = SkipActionBlock()
    result = await block.execute({}, params={"action": "status"})
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_allow_empty_input():
    block = EmptyInputBlock()
    result = await block.execute(None)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_text_output_field_attribute_exists():
    block = TextOutputFieldBlock()
    assert block.text_output_field == "translated"


@pytest.mark.asyncio
async def test_auto_validate_attribute_exists():
    block = AutoValidateOffBlock()
    assert block.auto_validate is False


@pytest.mark.asyncio
async def test_prepare_block_input_merges_params():
    block = RequiredFieldBlock()
    prepared = block._prepare_block_input({"a": 1}, {"b": 2})
    assert prepared["a"] == 1
    assert prepared["b"] == 2


@pytest.mark.asyncio
async def test_config_accessor_still_works():
    """Legacy ConfigAccessor behavior must survive the merge."""
    block = RequiredFieldBlock(config={"foo": "bar"})
    assert block.config["foo"] == "bar"
    assert block.config.get("foo") == "bar"


@pytest.mark.asyncio
async def test_mcp_tools_still_works():
    """mcp_tools() must still exist for backward compatibility."""
    block = RequiredFieldBlock()
    tools = block.mcp_tools()
    assert any("required_field_block_execute" in str(t) for t in tools)


@pytest.mark.asyncio
async def test_get_mcp_schema_still_works():
    """get_mcp_schema() must still exist for backward compatibility."""
    block = RequiredFieldBlock()
    schema = block.get_mcp_schema()
    assert schema["name"] == "required_field_block"
