"""Tests for Code Block."""

import pytest
import os
from app.blocks.code import CodeBlock

class TestCodeBlock:
    """Test suite for Code Block."""
    
    @pytest.fixture
    def block(self):
        return CodeBlock()
    
    @pytest.fixture
    def sample_python(self):
        return """
def hello():
    return "Hello, World!"

print(hello())
"""
    
    @pytest.mark.asyncio
    async def test_block_initialization(self, block):
        """Test block is properly initialized."""
        assert block.config.name == "code"
        assert block.config.version == "1.0"
    
    @pytest.mark.asyncio
    async def test_get_code_from_string(self, block):
        """Test _get_code with string input."""
        code = block._get_code("print('hello')")
        assert code == "print('hello')"
    
    @pytest.mark.asyncio
    async def test_get_code_from_dict(self, block):
        """Test _get_code with dict input."""
        code = block._get_code({"code": "print('hello')"})
        assert code == "print('hello')"
    
    @pytest.mark.asyncio
    async def test_analyze_code(self, block, sample_python):
        """Test code analysis."""
        result = await block.execute(
            sample_python,
            {"operation": "analyze", "language": "python"}
        )
        
        assert result["block"] == "code"
        assert "result" in result
        result_data = result["result"]
        assert result_data.get("operation") == "analyze"
        assert "lines" in result_data
    
    @pytest.mark.asyncio
    async def test_lint_code(self, block, sample_python):
        """Test code linting."""
        result = await block.execute(
            sample_python,
            {"operation": "lint", "language": "python"}
        )
        
        assert result["block"] == "code"
        assert "result" in result
        result_data = result["result"]
        assert "issues" in result_data
    
    @pytest.mark.asyncio
    async def test_format_code(self, block, sample_python):
        """Test code formatting."""
        result = await block.execute(
            sample_python,
            {"operation": "format", "language": "python"}
        )
        
        assert result["block"] == "code"
        assert "result" in result
        result_data = result["result"]
        assert "formatted_code" in result_data


class TestCodeBlockExecution:
    """Tests for code execution."""
    
    @pytest.mark.asyncio
    async def test_execute_python_print(self):
        """Test executing Python print statement."""
        block = CodeBlock()
        
        code = 'print("Hello from test")'
        result = await block.execute(
            code,
            {"operation": "execute", "language": "python"}
        )
        
        assert result["block"] == "code"
        assert "result" in result
        result_data = result["result"]
        assert "stdout" in result_data
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test execution with timeout."""
        block = CodeBlock()
        
        code = 'print("test")'
        result = await block.execute(
            code,
            {"operation": "execute", "language": "python", "timeout": 5}
        )
        
        assert result["block"] == "code"


class TestCodeBlockSecurity:
    """Security tests for Code Block."""
    
    @pytest.mark.asyncio
    async def test_dangerous_import_blocked(self):
        """Test that dangerous imports are blocked."""
        block = CodeBlock()
        
        code = "import os; os.system('ls')"
        result = await block.execute(
            code,
            {"operation": "execute", "language": "python"}
        )
        
        result_data = result["result"]
        # Should have error or not execute the dangerous code
        assert result_data.get("success") != True or "error" in result_data
