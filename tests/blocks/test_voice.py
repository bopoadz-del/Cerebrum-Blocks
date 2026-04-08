"""Tests for Voice Block."""

import pytest
from app.blocks.voice import VoiceBlock

class TestVoiceBlock:
    """Test suite for Voice Block."""
    
    @pytest.fixture
    def block(self):
        return VoiceBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "voice"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_detect_operation_tts(self, block):
        """Test detecting text-to-speech operation."""
        op = block._detect_operation("Hello World")
        assert op == "tts"
    
    @pytest.mark.asyncio
    async def test_detect_operation_stt(self, block):
        """Test detecting speech-to-text operation."""
        op = block._detect_operation({"audio_path": "/path/to/audio.mp3"})
        assert op == "stt"
    
    @pytest.mark.asyncio
    async def test_get_text_from_string(self, block):
        """Test _get_text with string."""
        text = block._get_text("Hello")
        assert text == "Hello"
    
    @pytest.mark.asyncio
    async def test_get_text_from_dict(self, block):
        """Test _get_text with dict."""
        text = block._get_text({"text": "Hello"})
        assert text == "Hello"
    
    @pytest.mark.asyncio
    async def test_process_tts_mock(self, block):
        """Test TTS with mock provider."""
        result = await block.execute(
            "Hello World",
            {"operation": "tts", "provider": "mock"}
        )
        
        assert result["block"] == "voice"
        assert "result" in result
        result_data = result["result"]
        assert result_data.get("operation") == "tts"


class TestVoiceBlockEdgeCases:
    """Edge case tests for Voice Block."""
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test handling of invalid operation."""
        block = VoiceBlock()
        
        result = await block.execute("input", {"operation": "invalid"})
        assert result["result"].get("error") is not None
    
    @pytest.mark.asyncio
    async def test_auto_detection(self):
        """Test auto operation detection."""
        block = VoiceBlock()
        
        # Should detect TTS from string
        result = await block.execute("Hello", {})
        assert result["block"] == "voice"
