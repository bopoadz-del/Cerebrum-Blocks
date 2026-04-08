"""Tests for PDF Block."""

import pytest
import os
from app.blocks.pdf import PDFBlock

class TestPDFBlock:
    """Test suite for PDF Block."""
    
    @pytest.fixture
    def block(self):
        return PDFBlock()
    
    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a sample PDF file for testing."""
        # For testing without actual PDF, we'll mock
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 mock pdf content")
        return str(pdf_path)
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "pdf"
        assert block.config.version == "1.0"
        assert "PDF" in block.config.description
    
    @pytest.mark.asyncio
    async def test_process_nonexistent_file(self, block):
        """Test processing a non-existent file raises error."""
        with pytest.raises((FileNotFoundError, ValueError)):
            await block.process({"file_path": "/nonexistent/file.pdf"})
    
    @pytest.mark.asyncio
    async def test_process_mock_pdf(self, block, sample_pdf_path):
        """Test processing a mock PDF file."""
        result = await block.execute({"file_path": sample_pdf_path}, {"extract_text": True})
        
        assert result["block"] == "pdf"
        assert "request_id" in result
        assert "status" in result
        assert "result" in result
        assert "processing_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_get_file_path_from_string(self, block):
        """Test _get_file_path with string input."""
        path = block._get_file_path("/path/to/file.pdf")
        assert path == "/path/to/file.pdf"
    
    @pytest.mark.asyncio
    async def test_get_file_path_from_dict_with_path(self, block):
        """Test _get_file_path with dict containing file_path."""
        path = block._get_file_path({"file_path": "/path/to/file.pdf"})
        assert path == "/path/to/file.pdf"
    
    @pytest.mark.asyncio
    async def test_get_file_path_from_dict_with_source_id(self, block):
        """Test _get_file_path with dict containing source_id."""
        path = block._get_file_path({"source_id": "abc123"})
        assert "/app/data/abc123" in path
    
    @pytest.mark.asyncio
    async def test_stats(self, block):
        """Test getting block statistics."""
        stats = block.get_stats()
        assert stats["name"] == "pdf"
        assert stats["version"] == "1.0"
        assert "execution_count" in stats


class TestPDFBlockIntegration:
    """Integration tests for PDF Block."""
    
    @pytest.mark.asyncio
    async def test_pdf_chain_compatibility(self):
        """Test PDF block works in a chain."""
        from app.core import CerebrumClient, chain
        
        client = CerebrumClient()
        chain_builder = chain(client)
        
        # Just verify chain building works
        chain_builder.then("pdf", {"extract_text": True})
        assert len(chain_builder.steps) == 1
        assert chain_builder.steps[0]["block"] == "pdf"
