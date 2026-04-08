"""Tests for Chat Block."""

import pytest
from app.blocks.chat import ChatBlock

class TestChatBlock:
    """Test suite for Chat Block."""
    
    @pytest.fixture
    def block(self):
        return ChatBlock()
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "chat"
        assert block.config.version == "1.0"
        assert block.config.requires_api_key == True
    
    @pytest.mark.asyncio
    async def test_build_messages_from_string(self, block):
        """Test building messages from string input."""
        messages = block._build_messages("Hello", "", "You are helpful.")
        assert len(messages) >= 1
        assert messages[0]["role"] == "system"
    
    @pytest.mark.asyncio
    async def test_build_messages_from_list(self, block):
        """Test building messages from list input."""
        input_msgs = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
        messages = block._build_messages(input_msgs, "", "")
        assert messages == input_msgs
    
    @pytest.mark.asyncio
    async def test_build_messages_from_dict_with_text(self, block):
        """Test building messages from dict with text."""
        messages = block._build_messages({"text": "Hello"}, "", "")
        assert any(m["content"] == "Hello" for m in messages)
    
    @pytest.mark.asyncio
    async def test_process_mock_provider(self, block):
        """Test processing with mock provider."""
        result = await block.execute("Hello", {"provider": "mock"})
        
        assert result["block"] == "chat"
        assert result["status"] == "success"
        assert "result" in result
        assert "text" in result["result"]
    
    @pytest.mark.asyncio
    async def test_process_with_prompt(self, block):
        """Test processing with a custom prompt."""
        result = await block.execute(
            "Tell me a joke",
            {"provider": "mock", "prompt": "Be funny"}
        )
        
        assert result["block"] == "chat"
        assert "result" in result


class TestChatBlockParams:
    """Tests for Chat Block parameter handling."""
    
    @pytest.mark.asyncio
    async def test_default_parameters(self):
        """Test default parameter values."""
        block = ChatBlock()
        
        result = await block.execute("Hello", {"provider": "mock"})
        result_data = result["result"]
        
        # Should have default values
        assert "text" in result_data
    
    @pytest.mark.asyncio
    async def test_custom_max_tokens(self):
        """Test custom max_tokens parameter."""
        block = ChatBlock()
        
        result = await block.execute("Hello", {
            "provider": "mock",
            "max_tokens": 500
        })
        
        assert result["block"] == "chat"


class TestChatBlockChainIntegration:
    """Tests for Chat Block in chain context."""
    
    @pytest.mark.asyncio
    async def test_chain_result_input(self):
        """Test processing chain result input."""
        block = ChatBlock()
        
        chain_input = {
            "result": {"text": "Previous block output"}
        }
        
        messages = block._build_messages(chain_input, "", "")
        assert any("Previous block output" in str(m.get("content", "")) for m in messages)
