"""
MCP Registry - Block capability discovery

This is the CONTRACT layer. It tells orchestrator:
- What blocks exist
- What each block can do (MCP tools)
- What inputs/outputs they expect

Orchestrator uses this for discovery, then calls .execute() directly.
"""
from typing import Dict, List, Any
from app.blocks import BLOCK_REGISTRY


class MCPRegistry:
    """
    Registry of block MCP schemas.

    This is the source of truth for block capabilities.
    Orchestrator consults this before routing, but execution is direct.
    """

    def __init__(self, block_registry: Dict):
        self.block_registry = block_registry
        self._schemas_cache = {}

    def get_block_schema(self, block_name: str) -> Dict:
        """Get MCP schema for a specific block"""
        if block_name not in self._schemas_cache:
            if block_name not in self.block_registry:
                raise ValueError(f"Block '{block_name}' not in registry")

            block_class = self.block_registry[block_name]
            block_instance = block_class()

            self._schemas_cache[block_name] = block_instance.get_mcp_schema()

        return self._schemas_cache[block_name]

    def get_all_schemas(self) -> Dict[str, Dict]:
        """Get all block schemas (for capability discovery)"""
        schemas = {}
        for block_name in self.block_registry.keys():
            try:
                schemas[block_name] = self.get_block_schema(block_name)
            except Exception:
                pass  # Skip broken blocks

        return schemas

    def get_tools_for_block(self, block_name: str) -> List[Dict]:
        """Get MCP tool definitions for a block"""
        schema = self.get_block_schema(block_name)
        return schema.get('tools', [])

    def find_blocks_with_capability(self, capability: str) -> List[str]:
        """Find blocks that have a specific capability/tag"""
        matching = []

        for block_name, schema in self.get_all_schemas().items():
            tags = schema.get('metadata', {}).get('tags', [])
            if capability in tags:
                matching.append(block_name)

        return matching

    def get_stats(self) -> Dict:
        """Registry statistics"""
        schemas = self.get_all_schemas()

        total_tools = sum(
            len(schema.get('tools', []))
            for schema in schemas.values()
        )

        return {
            "total_blocks": len(schemas),
            "total_tools": total_tools,
            "blocks_by_layer": self._group_by_layer(schemas),
            "blocks_by_tag": self._group_by_tag(schemas)
        }

    def _group_by_layer(self, schemas: Dict) -> Dict[int, int]:
        """Group blocks by layer"""
        layers = {}
        for schema in schemas.values():
            layer = schema.get('metadata', {}).get('layer', 0)
            layers[layer] = layers.get(layer, 0) + 1
        return layers

    def _group_by_tag(self, schemas: Dict) -> Dict[str, int]:
        """Group blocks by tag"""
        tags = {}
        for schema in schemas.values():
            for tag in schema.get('metadata', {}).get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1
        return tags


# Global registry instance
mcp_registry = MCPRegistry(BLOCK_REGISTRY)
