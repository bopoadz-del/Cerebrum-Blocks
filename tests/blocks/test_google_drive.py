"""Tests for Google Drive Block."""

import pytest
import os
from app.blocks.google_drive import GoogleDriveBlock

class TestGoogleDriveBlock:
    """Test suite for Google Drive Block."""
    
    @pytest.fixture
    def block(self):
        return GoogleDriveBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "google_drive"
        assert block.config.version == "1.0"
        assert block.config.requires_api_key == True
    
    @pytest.mark.asyncio
    async def test_get_file_path_from_string(self, block):
        """Test _get_file_path with string input."""
        path = block._get_file_path("/path/to/file.txt")
        assert path == "/path/to/file.txt"
    
    @pytest.mark.asyncio
    async def test_get_file_path_from_dict(self, block):
        """Test _get_file_path with dict input."""
        path = block._get_file_path({"file_path": "/path/to/file.txt"})
        assert path == "/path/to/file.txt"
    
    @pytest.mark.asyncio
    async def test_list_files_mock(self, block):
        """Test list files with mock (no auth)."""
        result = await block.execute({}, {"operation": "list"})
        
        assert result["block"] == "google_drive"
        assert "result" in result
        result_data = result["result"]
        # Should return mock response when not authenticated
        assert result_data.get("mock") == True or result_data.get("operation") == "list"
    
    @pytest.mark.asyncio
    async def test_search_files_mock(self, block):
        """Test search files with mock."""
        result = await block.execute(
            {},
            {"operation": "search", "query": "document"}
        )
        
        assert result["block"] == "google_drive"
        assert "result" in result


class TestGoogleDriveOperations:
    """Tests for specific Google Drive operations."""
    
    @pytest.mark.asyncio
    async def test_create_folder_mock(self):
        """Test create folder with mock."""
        block = GoogleDriveBlock()
        
        result = await block.execute(
            {},
            {"operation": "create_folder", "folder_name": "TestFolder"}
        )
        
        result_data = result["result"]
        assert result_data.get("mock") == True or result_data.get("operation") == "create_folder"
    
    @pytest.mark.asyncio
    async def test_get_metadata_mock(self):
        """Test get metadata with mock."""
        block = GoogleDriveBlock()
        
        result = await block.execute(
            {},
            {"operation": "get_metadata", "file_id": "mock123"}
        )
        
        result_data = result["result"]
        assert result_data.get("mock") == True or result_data.get("operation") == "get_metadata"


class TestGoogleDriveSecurity:
    """Security tests for Google Drive Block."""
    
    @pytest.mark.asyncio
    async def test_missing_file_id_handling(self):
        """Test handling of missing file ID."""
        block = GoogleDriveBlock()
        
        result = await block.execute(
            {},
            {"operation": "delete"}  # No file_id provided
        )
        
        result_data = result["result"]
        assert "error" in result_data or result_data.get("mock") == True
