"""Integration tests for the MCP server adapter."""

import asyncio
import json
import os
import sys

import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

pytestmark = pytest.mark.asyncio


class TestMcpServerStdio:
    """Test MCP server over stdio transport using the official client SDK."""

    async def test_list_tools(self):
        """All blocks should be exposed as MCP tools."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server"],
            env=None,
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()

        assert len(tools.tools) > 0
        names = [t.name for t in tools.tools]

        # Core blocks
        assert "cerebrum-chat" in names
        assert "cerebrum-pdf" in names
        assert "cerebrum-ocr" in names

        # Containers
        assert "cerebrum-construction" in names
        assert "cerebrum-legal" in names
        assert "cerebrum-medical" in names

        # Meta
        assert "cerebrum-chain" in names

    async def test_call_tool_chat_mock(self):
        """Calling a block via MCP should return standard Cerebrum output."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server"],
            env=None,
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "cerebrum-chat",
                    {"input": "Hello", "params": {"provider": "mock"}},
                )

        assert len(result.content) >= 1
        text = result.content[0].text
        data = json.loads(text)

        # Standard Cerebrum envelope
        assert data["block"] == "chat"
        assert "request_id" in data
        assert "status" in data
        assert "result" in data

    async def test_call_tool_unknown_block(self):
        """Calling an unknown tool should return a graceful error."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server"],
            env=None,
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "cerebrum-nonexistent-block-xyz",
                    {"input": "test"},
                )

        text = result.content[0].text
        assert "not found" in text.lower() or "unknown" in text.lower()

    async def test_call_chain_tool(self):
        """The cerebrum-chain meta-tool should accept steps."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server"],
            env=None,
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "cerebrum-chain",
                    {
                        "steps": [
                            {"block": "chat", "params": {"provider": "mock"}},
                        ],
                        "initial_input": "Hello",
                    },
                )

        text = result.content[0].text
        data = json.loads(text)
        # Should return orchestrator envelope
        assert "block" in data
        assert data["block"] == "orchestrator"
