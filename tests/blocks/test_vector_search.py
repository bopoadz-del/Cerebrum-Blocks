"""Tests for Vector Search Block."""

import pytest
import os
from app.blocks.vector_search import VectorSearchBlock, Document

class TestVectorSearchBlock:
    """Test suite for Vector Search Block."""
    
    @pytest.fixture
    def block(self):
        return VectorSearchBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "vector_search"
        assert block.config.version == "1.0"
        assert "vector" in block.config.description.lower()
    
    @pytest.mark.asyncio
    async def test_get_query_from_string(self, block):
        """Test _get_query with string input."""
        query = block._get_query("semantic search query")
        assert query == "semantic search query"
    
    @pytest.mark.asyncio
    async def test_get_query_from_dict(self, block):
        """Test _get_query with dict input."""
        query = block._get_query({"query": "test query"})
        assert query == "test query"
    
    @pytest.mark.asyncio
    async def test_get_documents_from_list(self, block):
        """Test _get_documents with list input."""
        docs = block._get_documents([
            {"text": "doc 1", "metadata": {}},
            {"text": "doc 2", "metadata": {}}
        ])
        assert len(docs) == 2
        assert docs[0]["text"] == "doc 1"
    
    @pytest.mark.asyncio
    async def test_get_texts_from_string(self, block):
        """Test _get_texts with string input."""
        texts = block._get_texts("single text")
        assert texts == ["single text"]
    
    @pytest.mark.asyncio
    async def test_get_texts_from_list(self, block):
        """Test _get_texts with list input."""
        texts = block._get_texts(["text 1", "text 2"])
        assert len(texts) == 2
    
    @pytest.mark.asyncio
    async def test_generate_id(self, block):
        """Test ID generation from text."""
        id1 = block._generate_id("test text")
        id2 = block._generate_id("test text")
        id3 = block._generate_id("different text")
        
        assert id1 == id2  # Same text = same ID
        assert id1 != id3  # Different text = different ID
        assert len(id1) == 16
    
    @pytest.mark.asyncio
    async def test_search_mock(self, block):
        """Test search without ChromaDB installed."""
        result = await block.execute(
            "test query",
            {"operation": "search", "top_k": 3}
        )
        
        assert result["block"] == "vector_search"
        assert "result" in result
        result_data = result["result"]
        
        if result_data.get("mock"):
            assert "matches" in result_data
            assert "message" in result_data
    
    @pytest.mark.asyncio
    async def test_list_collections_mock(self, block):
        """Test list collections without ChromaDB."""
        result = await block.execute(
            {},
            {"operation": "list_collections"}
        )
        
        assert result["block"] == "vector_search"
        result_data = result["result"]
        assert "collections" in result_data
    
    @pytest.mark.asyncio
    async def test_count_mock(self, block):
        """Test count without ChromaDB."""
        result = await block.execute(
            {},
            {"operation": "count", "collection": "test"}
        )
        
        assert result["block"] == "vector_search"
        result_data = result["result"]
        assert "count" in result_data


class TestVectorSearchOperations:
    """Tests for vector search operations."""
    
    @pytest.mark.asyncio
    async def test_embed_operation_mock(self):
        """Test embed operation."""
        block = VectorSearchBlock()
        
        result = await block.execute(
            "test text",
            {"operation": "embed"}
        )
        
        assert result["block"] == "vector_search"
        result_data = result["result"]
        assert "embeddings" in result_data
        assert "dimensions" in result_data
    
    @pytest.mark.asyncio
    async def test_add_documents_mock(self):
        """Test add documents operation."""
        block = VectorSearchBlock()
        
        docs = [
            {"text": "First document", "metadata": {"source": "test"}},
            {"text": "Second document", "metadata": {"source": "test"}}
        ]
        
        result = await block.execute(
            docs,
            {"operation": "add", "collection": "test_collection"}
        )
        
        assert result["block"] == "vector_search"
        result_data = result["result"]
        assert result_data["document_count"] == 2
    
    @pytest.mark.asyncio
    async def test_create_collection_mock(self):
        """Test create collection operation."""
        block = VectorSearchBlock()
        
        result = await block.execute(
            "my_collection",
            {"operation": "create_collection"}
        )
        
        assert result["block"] == "vector_search"
        result_data = result["result"]
        assert result_data["collection"] == "my_collection"


class TestVectorSearchIntegration:
    """Integration tests for Vector Search."""
    
    @pytest.mark.asyncio
    async def test_full_vector_workflow_mock(self):
        """Test full workflow: create -> add -> search."""
        block = VectorSearchBlock()
        
        # 1. Create collection
        create_result = await block.execute(
            "test_collection",
            {"operation": "create_collection"}
        )
        
        # 2. Add documents
        docs = [
            {"text": "Machine learning is amazing", "metadata": {"topic": "ml"}},
            {"text": "Deep learning is a subset of ML", "metadata": {"topic": "dl"}},
            {"text": "Neural networks are powerful", "metadata": {"topic": "nn"}}
        ]
        
        add_result = await block.execute(
            docs,
            {"operation": "add", "collection": "test_collection"}
        )
        
        # 3. Search
        search_result = await block.execute(
            "machine learning",
            {"operation": "search", "collection": "test_collection", "top_k": 2}
        )
        
        assert search_result["block"] == "vector_search"
        result_data = search_result["result"]
        assert "matches" in result_data or result_data.get("mock") == True
    
    @pytest.mark.asyncio
    async def test_delete_operation(self):
        """Test delete documents."""
        block = VectorSearchBlock()
        
        result = await block.execute(
            {},
            {"operation": "delete", "collection": "test", "ids": ["id1", "id2"]}
        )
        
        assert result["block"] == "vector_search"


class TestVectorSearchConfig:
    """Tests for configuration and setup."""
    
    def test_default_collection(self):
        """Test default collection setting."""
        block = VectorSearchBlock()
        assert block.default_collection == "default" or os.getenv("VECTOR_COLLECTION")
    
    def test_persist_directory(self):
        """Test persist directory setting."""
        block = VectorSearchBlock()
        assert block.persist_directory is not None
        assert "/chroma_db" in block.persist_directory or "chroma" in block.persist_directory
