"""Tests for Local Drive Block."""

import pytest
import os
import tempfile
import shutil
from app.blocks.local_drive import LocalDriveBlock

class TestLocalDriveBlock:
    """Test suite for Local Drive Block."""
    
    @pytest.fixture
    def block(self):
        return LocalDriveBlock()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "local_drive"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_safe_path_resolution(self, block, temp_dir):
        """Test safe path resolution."""
        block.base_path = temp_dir
        
        safe = block._safe_path("/subdir/file.txt")
        assert safe.startswith(temp_dir)
        assert "subdir" in safe
    
    @pytest.mark.asyncio
    async def test_list_files(self, block, temp_dir):
        """Test listing files."""
        block.base_path = temp_dir
        
        # Create test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        result = await block.execute({}, {"operation": "list", "folder_path": "/"})
        
        assert result["block"] == "local_drive"
        assert result["status"] == "success"
        result_data = result["result"]
        assert result_data["file_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_create_folder(self, block, temp_dir):
        """Test creating a folder."""
        block.base_path = temp_dir
        
        result = await block.execute(
            {},
            {"operation": "create_folder", "folder_name": "NewFolder", "parent_path": "/"}
        )
        
        assert result["status"] == "success"
        result_data = result["result"]
        assert result_data["created"] == True
        assert os.path.exists(os.path.join(temp_dir, "NewFolder"))
    
    @pytest.mark.asyncio
    async def test_write_and_read_file(self, block, temp_dir):
        """Test writing and reading a file."""
        block.base_path = temp_dir
        
        # Write file
        write_result = await block.execute(
            {},
            {"operation": "write", "file_path": "/test.txt", "content": "Hello World"}
        )
        
        assert write_result["status"] == "success"
        
        # Read file
        read_result = await block.execute(
            {},
            {"operation": "read", "file_path": "/test.txt"}
        )
        
        assert read_result["status"] == "success"
        assert read_result["result"]["content"] == "Hello World"
    
    @pytest.mark.asyncio
    async def test_delete_file(self, block, temp_dir):
        """Test deleting a file."""
        block.base_path = temp_dir
        
        # Create file
        test_file = os.path.join(temp_dir, "to_delete.txt")
        with open(test_file, "w") as f:
            f.write("delete me")
        
        # Delete file
        result = await block.execute(
            {},
            {"operation": "delete", "file_path": "/to_delete.txt"}
        )
        
        assert result["status"] == "success"
        assert result["result"]["deleted"] == True
        assert not os.path.exists(test_file)


class TestLocalDriveMetadata:
    """Tests for metadata operations."""
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test getting file metadata."""
        block = LocalDriveBlock()
        temp_dir = tempfile.mkdtemp()
        block.base_path = temp_dir
        
        try:
            # Create test file
            test_file = os.path.join(temp_dir, "meta_test.txt")
            with open(test_file, "w") as f:
                f.write("content for metadata test")
            
            result = await block.execute(
                {},
                {"operation": "get_metadata", "file_path": "/meta_test.txt", "include_hash": True}
            )
            
            assert result["status"] == "success"
            result_data = result["result"]
            assert "size" in result_data
            assert "modified" in result_data
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_search_files(self):
        """Test searching for files."""
        block = LocalDriveBlock()
        temp_dir = tempfile.mkdtemp()
        block.base_path = temp_dir
        
        try:
            # Create test files
            open(os.path.join(temp_dir, "find_me.txt"), "w").close()
            open(os.path.join(temp_dir, "other.txt"), "w").close()
            
            result = await block.execute(
                {},
                {"operation": "search", "query": "find", "folder_path": "/"}
            )
            
            assert result["status"] == "success"
            result_data = result["result"]
            assert result_data["match_count"] >= 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestLocalDriveSecurity:
    """Security tests for Local Drive Block."""
    
    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self):
        """Test that path traversal is blocked."""
        block = LocalDriveBlock()
        temp_dir = tempfile.mkdtemp()
        block.base_path = temp_dir
        
        try:
            # Try to access parent directory
            with pytest.raises(ValueError):
                block._safe_path("../../../etc/passwd")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
