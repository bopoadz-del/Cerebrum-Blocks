"""Tests for OneDrive Block."""

import pytest
from app.blocks.onedrive import OneDriveBlock

class TestOneDriveBlock:
    """Test suite for OneDrive Block."""
    
    @pytest.fixture
    def block(self):
        return OneDriveBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "onedrive"
        assert block.config.version == "1.0"
        assert block.config.requires_api_key == True
    
    @pytest.mark.asyncio
    async def test_list_files_mock(self, block):
        """Test list files with mock (no auth)."""
        result = await block.execute({}, {"operation": "list"})
        
        assert result["block"] == "onedrive"
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_create_folder_mock(self, block):
        """Test create folder with mock."""
        result = await block.execute(
            {},
            {"operation": "create_folder", "folder_name": "Test"}
        )
        
        result_data = result["result"]
        assert result_data.get("mock") == True or result_data.get("operation") == "create_folder"
    
    @pytest.mark.asyncio
    async def test_search_files_mock(self, block):
        """Test search files with mock."""
        result = await block.execute(
            {},
            {"operation": "search", "query": "document"}
        )
        
        assert result["block"] == "onedrive"


class TestOneDriveShare:
    """Tests for OneDrive sharing functionality."""
    
    @pytest.mark.asyncio
    async def test_share_file_mock(self):
        """Test share file with mock."""
        block = OneDriveBlock()
        
        result = await block.execute(
            {},
            {"operation": "share", "file_id": "mock123", "link_type": "view"}
        )
        
        result_data = result["result"]
        assert result_data.get("mock") == True or result_data.get("operation") == "share"
