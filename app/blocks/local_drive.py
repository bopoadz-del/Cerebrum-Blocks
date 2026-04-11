"""Local Drive Block - Local filesystem access"""

import os
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class LocalDriveBlock(UniversalBlock):
    """Local filesystem operations"""
    
    name = "local_drive"
    version = "1.0"
    layer = 4
    tags = ["integration", "storage", "local"]
    requires = []
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """List, read, or write local files"""
        path = input_data if isinstance(input_data, str) else "./"
        
        try:
            files = os.listdir(path) if os.path.isdir(path) else []
            return {
                "status": "success",
                "path": path,
                "files": files[:20]  # Limit results
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
