"""Tests for Web Block."""

import pytest
from app.blocks.web import WebBlock

class TestWebBlock:
    """Test suite for Web Block."""
    
    @pytest.fixture
    def block(self):
        return WebBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "web"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_get_url_from_string(self, block):
        """Test _get_url with string input."""
        url = block._get_url("https://example.com")
        assert url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_get_url_from_dict(self, block):
        """Test _get_url with dict input."""
        url = block._get_url({"url": "https://example.com"})
        assert url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_parse_html(self, block):
        """Test HTML parsing."""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is a test.</p>
                <a href="https://example.com">Link</a>
            </body>
        </html>
        """
        
        result = await block.execute(
            html,
            {"operation": "html_parse"}
        )
        
        assert result["block"] == "web"
        assert "result" in result
        result_data = result["result"]
        assert result_data.get("title") == "Test Page"
        assert "Hello World" in result_data.get("headings", [])


class TestWebBlockParseHTML:
    """Tests for HTML parsing."""
    
    @pytest.mark.asyncio
    async def test_parse_extracts_links(self):
        """Test that HTML parsing extracts links."""
        block = WebBlock()
        
        html = '<a href="https://example.com">Example</a>'
        result = await block.execute(html, {"operation": "html_parse"})
        result_data = result["result"]
        
        links = result_data.get("links", [])
        assert len(links) > 0
        assert links[0]["url"] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_parse_extracts_paragraphs(self):
        """Test that HTML parsing extracts paragraphs."""
        block = WebBlock()
        
        html = '<p>First paragraph</p><p>Second paragraph</p>'
        result = await block.execute(html, {"operation": "html_parse"})
        result_data = result["result"]
        
        paragraphs = result_data.get("paragraphs", [])
        assert "First paragraph" in paragraphs
        assert "Second paragraph" in paragraphs
    
    @pytest.mark.asyncio
    async def test_parse_extracts_headings(self):
        """Test that HTML parsing extracts headings."""
        block = WebBlock()
        
        html = '<h1>Title</h1><h2>Subtitle</h2>'
        result = await block.execute(html, {"operation": "html_parse"})
        result_data = result["result"]
        
        headings = result_data.get("headings", [])
        assert "Title" in headings
        assert "Subtitle" in headings
