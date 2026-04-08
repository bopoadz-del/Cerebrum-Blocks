"""Tests for Translate Block."""

import pytest
from app.blocks.translate import TranslateBlock

class TestTranslateBlock:
    """Test suite for Translate Block."""
    
    @pytest.fixture
    def block(self):
        return TranslateBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "translate"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_get_text_from_string(self, block):
        """Test _get_text with string input."""
        text = block._get_text("Hello World")
        assert text == "Hello World"
    
    @pytest.mark.asyncio
    async def test_get_text_from_dict(self, block):
        """Test _get_text with dict input."""
        text = block._get_text({"text": "Hello World"})
        assert text == "Hello World"
    
    @pytest.mark.asyncio
    async def test_process_mock_translation(self, block):
        """Test translation with mock provider."""
        result = await block.execute(
            "Hello World",
            {"provider": "mock", "target": "es", "source": "en"}
        )
        
        assert result["block"] == "translate"
        assert result["status"] == "success"
        assert "result" in result
        result_data = result["result"]
        assert "translated_text" in result_data
        assert result_data["target_language"] == "es"


class TestTranslateBlockLanguages:
    """Tests for different language combinations."""
    
    @pytest.mark.asyncio
    async def test_english_to_spanish(self):
        """Test English to Spanish translation."""
        block = TranslateBlock()
        
        result = await block.execute(
            "Hello",
            {"provider": "mock", "target": "es", "source": "en"}
        )
        
        assert result["block"] == "translate"
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_auto_source_detection(self):
        """Test auto source language detection."""
        block = TranslateBlock()
        
        result = await block.execute(
            "Hello",
            {"provider": "mock", "target": "fr", "source": "auto"}
        )
        
        result_data = result["result"]
        assert result_data["source_language"] == "auto"
