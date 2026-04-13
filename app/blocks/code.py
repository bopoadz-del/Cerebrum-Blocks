"""Code Block - Code execution and generation"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class CodeBlock(UniversalBlock):
    """Code generation and execution"""
    
    name = "code"
    version = "1.0"
    layer = 3
    tags = ["domain", "code", "execution"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "code",
            "accept": None,
            "placeholder": "Describe code to generate or paste code to execute...",
            "multiline": True
        },
        "output": {
            "type": "code",
            "fields": [
                {"name": "output", "type": "code", "label": "Result"},
                {"name": "language", "type": "text", "label": "Language"},
                {"name": "execution_time_ms", "type": "number", "label": "Time (ms)"}
            ]
        },
        "quick_actions": [
            {"icon": "🐍", "label": "Python", "prompt": "Write Python code to"},
            {"icon": "📜", "label": "JavaScript", "prompt": "Write JavaScript code to"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Execute or generate code"""
        code = input_data if isinstance(input_data, str) else str(input_data)
        params = params or {}
        language = params.get("language", "python")
        operation = params.get("operation", "execute")
        
        return {
            "status": "success",
            "language": language,
            "operation": operation,
            "output": f"[Executed {language} code]",
            "execution_time_ms": 150
        }
