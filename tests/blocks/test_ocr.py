"""Tests for OCR Block."""

import pytest
from PIL import Image
import io
from app.blocks.ocr import OCRBlock

class TestOCRBlock:
    """Test suite for OCR Block."""
    
    @pytest.fixture
    def block(self):
        return OCRBlock()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        img = Image.new("RGB", (100, 50), color="white")
        return img
    
    @pytest.fixture
    def sample_image_base64(self):
        """Create a sample base64 encoded image."""
        img = Image.new("RGB", (100, 50), color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        import base64
        return base64.b64encode(buffer.getvalue()).decode()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "ocr"
        assert block.config.version == "1.0"
        assert "OCR" in block.config.description
    
    @pytest.mark.asyncio
    async def test_load_image_from_pil(self, block, sample_image):
        """Test loading image from PIL Image."""
        loaded = block._load_image({"image": sample_image})
        assert loaded.size == (100, 50)
    
    @pytest.mark.asyncio
    async def test_load_image_from_base64(self, block, sample_image_base64):
        """Test loading image from base64 string."""
        loaded = block._load_image({"image_base64": sample_image_base64})
        assert loaded.size == (100, 50)
    
    @pytest.mark.asyncio
    async def test_detect_operation_analyze(self, block, sample_image):
        """Test operation detection for analyze."""
        op = block._detect_operation({"image": sample_image})
        assert op == "analyze"
    
    @pytest.mark.asyncio
    async def test_process_with_mock_image(self, block, sample_image):
        """Test processing with a mock image."""
        result = await block.execute({"image": sample_image}, {"language": "eng"})
        
        assert result["block"] == "ocr"
        assert "request_id" in result
        assert "result" in result
        assert "image_size" in result["result"]


class TestOCRBlockEdgeCases:
    """Edge case tests for OCR Block."""
    
    @pytest.mark.asyncio
    async def test_invalid_image_input(self):
        """Test handling of invalid image input."""
        block = OCRBlock()
        
        with pytest.raises(ValueError):
            block._load_image({"invalid": "input"})
    
    @pytest.mark.asyncio
    async def test_get_text_from_string(self):
        """Test _get_text with string input."""
        block = OCRBlock()
        text = block._get_text("Hello World")
        assert text == "Hello World"
    
    @pytest.mark.asyncio
    async def test_get_text_from_dict(self):
        """Test _get_text with dict input."""
        block = OCRBlock()
        text = block._get_text({"text": "Hello World"})
        assert text == "Hello World"
