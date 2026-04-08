"""Tests for Search Block."""

import pytest
from app.blocks.search import SearchBlock

class TestSearchBlock:
    """Test suite for Search Block."""
    
    @pytest.fixture
    def block(self):
        return SearchBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "search"
        assert block.config.version == "1.0"
        assert block.config.requires_api_key == True
    
    @pytest.mark.asyncio
    async def test_get_query_from_string(self, block):
        """Test _get_query with string input."""
        query = block._get_query("python tutorials")
        assert query == "python tutorials"
    
    @pytest.mark.asyncio
    async def test_get_query_from_dict(self, block):
        """Test _get_query with dict input."""
        query = block._get_query({"query": "python tutorials"})
        assert query == "python tutorials"
    
    @pytest.mark.asyncio
    async def test_get_query_from_text_dict(self, block):
        """Test _get_query with dict containing text."""
        query = block._get_query({"text": "python tutorials"})
        assert query == "python tutorials"
    
    @pytest.mark.asyncio
    async def test_process_mock_search(self, block):
        """Test search with mock provider."""
        result = await block.execute(
            "artificial intelligence",
            {"provider": "mock", "num_results": 5}
        )
        
        assert result["block"] == "search"
        assert result["status"] == "success"
        assert "result" in result
        result_data = result["result"]
        assert "results" in result_data
        assert result_data["query"] == "artificial intelligence"


class TestSearchBlockProviders:
    """Tests for different search providers."""
    
    @pytest.mark.asyncio
    async def test_mock_provider_returns_results(self):
        """Test that mock provider returns proper results."""
        block = SearchBlock()
        
        result = await block.execute("test", {"provider": "mock", "num_results": 3})
        result_data = result["result"]
        
        assert "results" in result_data
        assert result_data["total_results"] == 3
        assert len(result_data["results"]) == 3
    
    @pytest.mark.asyncio
    async def test_mock_provider_result_structure(self):
        """Test mock provider result structure."""
        block = SearchBlock()
        
        result = await block.execute("test", {"provider": "mock"})
        result_data = result["result"]
        
        for item in result_data["results"]:
            assert "title" in item
            assert "url" in item
            assert "snippet" in item
