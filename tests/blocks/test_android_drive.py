"""Tests for Android Drive Block."""

import pytest
from app.blocks.android_drive import AndroidDriveBlock

class TestAndroidDriveBlock:
    """Test suite for Android Drive Block."""
    
    @pytest.fixture
    def block(self):
        return AndroidDriveBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "android_drive"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_get_paths(self, block):
        """Test getting Android paths."""
        result = await block.execute({}, {"operation": "get_paths"})
        
        assert result["block"] == "android_drive"
        assert result["status"] == "success"
        result_data = result["result"]
        assert "paths" in result_data
        assert "shared_storage" in result_data["paths"]
        assert "downloads" in result_data["paths"]
    
    @pytest.mark.asyncio
    async def test_list_files_mock(self, block):
        """Test list files with mock (not Android env)."""
        result = await block.execute({}, {"operation": "list"})
        
        assert result["block"] == "android_drive"
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_scan_media_mock(self, block):
        """Test scan media with mock."""
        result = await block.execute(
            {},
            {"operation": "scan_media", "media_type": "images"}
        )
        
        assert result["block"] == "android_drive"
        result_data = result["result"]
        # Should return mock when not on Android
        assert result_data.get("mock") == True or result_data.get("files") is not None


class TestAndroidDriveMimeTypes:
    """Tests for MIME type detection."""
    
    @pytest.mark.asyncio
    async def test_jpeg_mime_type(self):
        """Test JPEG MIME type detection."""
        block = AndroidDriveBlock()
        mime = block._guess_mime_type("photo.jpg")
        assert mime == "image/jpeg"
    
    @pytest.mark.asyncio
    async def test_png_mime_type(self):
        """Test PNG MIME type detection."""
        block = AndroidDriveBlock()
        mime = block._guess_mime_type("image.png")
        assert mime == "image/png"
    
    @pytest.mark.asyncio
    async def test_pdf_mime_type(self):
        """Test PDF MIME type detection."""
        block = AndroidDriveBlock()
        mime = block._guess_mime_type("document.pdf")
        assert mime == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_mp4_mime_type(self):
        """Test MP4 MIME type detection."""
        block = AndroidDriveBlock()
        mime = block._guess_mime_type("video.mp4")
        assert mime == "video/mp4"
    
    @pytest.mark.asyncio
    async def test_unknown_mime_type(self):
        """Test unknown file MIME type."""
        block = AndroidDriveBlock()
        mime = block._guess_mime_type("file.xyz")
        assert mime == "application/octet-stream"


class TestAndroidDrivePathHandling:
    """Tests for path handling."""
    
    @pytest.mark.asyncio
    async def test_safe_path_file_uri(self):
        """Test handling file:// URIs."""
        block = AndroidDriveBlock()
        path = block._safe_path("file:///sdcard/Download/test.txt")
        assert path == "/sdcard/Download/test.txt"
    
    @pytest.mark.asyncio
    async def test_safe_path_content_uri(self):
        """Test handling content:// URIs."""
        block = AndroidDriveBlock()
        path = block._safe_path("content://media/external/downloads/123")
        assert path == "content://media/external/downloads/123"
    
    @pytest.mark.asyncio
    async def test_safe_path_relative(self):
        """Test handling relative paths."""
        block = AndroidDriveBlock()
        path = block._safe_path("Download/test.txt")
        assert "sdcard" in path or "Download" in path


class TestAndroidDriveEnvironment:
    """Tests for Android environment detection."""
    
    @pytest.mark.asyncio
    async def test_android_env_detection(self):
        """Test Android environment detection."""
        block = AndroidDriveBlock()
        # Will be False in test environment
        is_android = block._is_android_environment()
        assert isinstance(is_android, bool)
