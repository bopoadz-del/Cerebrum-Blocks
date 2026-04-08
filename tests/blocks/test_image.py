"""Tests for Image Block."""

import pytest
from PIL import Image
import io
import base64
from app.blocks.image import ImageBlock

class TestImageBlock:
    """Test suite for Image Block."""
    
    @pytest.fixture
    def block(self):
        return ImageBlock()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        return Image.new("RGB", (100, 100), color="red")
    
    @pytest.fixture
    def sample_image_base64(self):
        """Create a sample base64 encoded image."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "image"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_detect_operation_analyze(self, block, sample_image):
        """Test detecting analyze operation."""
        op = block._detect_operation({"image": sample_image})
        assert op == "analyze"
    
    @pytest.mark.asyncio
    async def test_detect_operation_generate(self, block):
        """Test detecting generate operation."""
        op = block._detect_operation("A red circle")
        assert op == "generate"
    
    @pytest.mark.asyncio
    async def test_load_image_from_pil(self, block, sample_image):
        """Test loading image from PIL Image."""
        loaded = block._load_image({"image": sample_image})
        assert loaded.size == (100, 100)
    
    @pytest.mark.asyncio
    async def test_load_image_from_base64(self, block, sample_image_base64):
        """Test loading image from base64."""
        loaded = block._load_image({"image_base64": sample_image_base64})
        assert loaded.size == (100, 100)
    
    @pytest.mark.asyncio
    async def test_get_prompt_from_string(self, block):
        """Test _get_prompt with string."""
        prompt = block._get_prompt("A cat")
        assert prompt == "A cat"
    
    @pytest.mark.asyncio
    async def test_process_analyze_mock(self, block, sample_image):
        """Test analyze with mock provider."""
        result = await block.execute(
            {"image": sample_image},
            {"operation": "analyze", "provider": "mock"}
        )
        
        assert result["block"] == "image"
        assert "result" in result
        result_data = result["result"]
        assert result_data.get("operation") == "analyze"
    
    @pytest.mark.asyncio
    async def test_process_generate_mock(self, block):
        """Test generate with mock provider."""
        result = await block.execute(
            "A beautiful landscape",
            {"operation": "generate", "provider": "mock"}
        )
        
        assert result["block"] == "image"
        assert "result" in result
        result_data = result["result"]
        assert "image_base64" in result_data


class TestImageBlockEdgeCases:
    """Edge case tests for Image Block."""
    
    @pytest.mark.asyncio
    async def test_invalid_image_input(self):
        """Test handling of invalid image input."""
        block = ImageBlock()
        
        with pytest.raises(ValueError):
            block._load_image({"invalid": "input"})
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_input(self):
        """Test handling of invalid prompt input."""
        block = ImageBlock()
        
        with pytest.raises(ValueError):
            block._get_prompt({"invalid": "input"})
