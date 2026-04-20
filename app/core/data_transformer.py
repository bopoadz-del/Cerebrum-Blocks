"""
DataTransformer - Convert between block output formats.

This module transforms block-specific output formats to standard types:
- PDF returns {"text": "...", "pages": 5} → transform to standard TextContent
- OCR returns {"result": {"text": "..."}} → extract and normalize
- Construction returns complex dict → wrap properly
"""

from typing import Any, Dict, List, Optional, Callable, Union
from .schema_registry import (
    TextContent,
    ImageContent,
    PDFContent,
    ChatMessage,
    ChatConversation,
    SearchResult,
    VectorEmbedding,
    FileContent,
    registry,
    get_registry
)


class DataTransformer:
    """
    DataTransformer - Converts block output formats to standard types.
    
    Each block may output data in its own format. DataTransformer
    normalizes these to standard types for interoperability.
    
    Example:
        pdf_output = {"text": "Hello", "pages": 5}
        text_content = transformer.transform(pdf_output, "TextContent")
        # Result: {"text": "Hello", "source": "pdf", "metadata": {...}}
    """
    
    _instance = None
    _transformers: Dict[str, Dict[str, Callable]] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_default_transformers()
        return cls._instance
    
    def _register_default_transformers(self):
        """Register all default transformers."""
        # PDFBlock output → various types
        self.register("pdf", "TextContent", self._pdf_to_text)
        self.register("pdf", "PDFContent", self._pdf_to_pdf_content)
        
        # OCRBlock output → various types
        self.register("ocr", "TextContent", self._ocr_to_text)
        
        # ChatBlock output → various types
        self.register("chat", "TextContent", self._chat_to_text)
        self.register("chat", "ChatMessage", self._chat_to_message)
        
        # SearchBlock output → various types
        self.register("search", "SearchResult", self._search_to_result)
        
        # ImageBlock output → various types
        self.register("image", "ImageContent", self._image_to_content)
        
        # File blocks → FileContent
        self.register("google_drive", "FileContent", self._drive_to_file)
        self.register("onedrive", "FileContent", self._drive_to_file)
        self.register("local_drive", "FileContent", self._drive_to_file)
        self.register("android_drive", "FileContent", self._drive_to_file)
        
        # Vector blocks
        self.register("vector_search", "VectorEmbedding", self._vector_to_embedding)
        self.register("zvec", "VectorEmbedding", self._zvec_to_embedding)
        
        # Voice blocks
        self.register("voice", "AudioContent", self._voice_to_audio)
        
        # Translate blocks
        self.register("translate", "TranslationResult", self._translate_to_result)
        
        # Code blocks
        self.register("code", "CodeResult", self._code_to_result)
    
    # ========================================================================
    # TRANSFORMER METHODS
    # ========================================================================
    
    def _pdf_to_text(self, data: Dict) -> Dict:
        """Transform PDF block output to TextContent."""
        # Handle UniversalBlock wrapped result
        if "result" in data:
            data = data["result"]
        
        return {
            "text": data.get("text", ""),
            "source": "pdf",
            "metadata": {
                "pages": data.get("pages", 0),
                "filename": data.get("filename", ""),
                "status": data.get("status", "unknown")
            }
        }
    
    def _pdf_to_pdf_content(self, data: Dict) -> Dict:
        """Transform PDF block output to PDFContent."""
        if "result" in data:
            data = data["result"]
        
        return {
            "file_path": data.get("file_path", ""),
            "filename": data.get("filename", ""),
            "pages": data.get("pages", 0),
            "text": data.get("text", ""),
            "metadata": {
                "status": data.get("status", "unknown")
            }
        }
    
    def _ocr_to_text(self, data: Dict) -> Dict:
        """Transform OCR block output to TextContent."""
        if "result" in data:
            data = data["result"]
        
        return {
            "text": data.get("text", ""),
            "source": "ocr",
            "metadata": {
                "confidence": data.get("confidence", 0),
                "word_count": data.get("word_count", 0),
                "engine": data.get("engine", ""),
                "preprocessed": data.get("preprocessed", False)
            }
        }
    
    def _chat_to_text(self, data: Dict) -> Dict:
        """Transform Chat block output to TextContent."""
        if "result" in data:
            data = data["result"]
        
        return {
            "text": data.get("text", ""),
            "source": "chat",
            "metadata": {
                "provider": data.get("provider", ""),
                "model": data.get("model", ""),
                "tokens": data.get("tokens", {})
            }
        }
    
    def _chat_to_message(self, data: Dict) -> Dict:
        """Transform Chat block output to ChatMessage."""
        if "result" in data:
            data = data["result"]
        
        import time
        return {
            "role": "assistant",
            "content": data.get("text", ""),
            "timestamp": str(int(time.time())),
            "metadata": {
                "provider": data.get("provider", ""),
                "model": data.get("model", ""),
                "tokens": data.get("tokens", {})
            }
        }
    
    def _search_to_result(self, data: Dict) -> Dict:
        """Transform Search block output to SearchResult."""
        if "result" in data:
            data = data["result"]
        
        return {
            "query": data.get("query", ""),
            "results": data.get("results", []),
            "total_found": data.get("total_found", 0),
            "source": data.get("provider", "search"),
            "metadata": data.get("metadata", {})
        }
    
    def _image_to_content(self, data: Dict) -> Dict:
        """Transform Image block output to ImageContent."""
        if "result" in data:
            data = data["result"]
        
        return {
            "image_data": data.get("image_data", data.get("image_url", "")),
            "format": data.get("format", "png"),
            "width": data.get("width", 0),
            "height": data.get("height", 0),
            "source": data.get("provider", "image"),
            "metadata": {
                "description": data.get("description", ""),
                "status": data.get("status", "unknown")
            }
        }
    
    def _drive_to_file(self, data: Dict) -> Dict:
        """Transform Drive block output to FileContent."""
        if "result" in data:
            data = data["result"]
        
        return {
            "file_path": data.get("file_path", data.get("path", "")),
            "filename": data.get("filename", data.get("name", "")),
            "content": data.get("content", ""),
            "mime_type": data.get("mime_type", data.get("content_type", "")),
            "size": data.get("size", 0),
            "metadata": data.get("metadata", {})
        }
    
    def _vector_to_embedding(self, data: Dict) -> Dict:
        """Transform VectorSearch block output to VectorEmbedding."""
        if "result" in data:
            data = data["result"]
        
        return {
            "vector": data.get("embedding", data.get("vector", [])),
            "dimension": data.get("dimension", len(data.get("embedding", []))),
            "text": data.get("text", ""),
            "id": data.get("id", ""),
            "metadata": data.get("metadata", {})
        }
    
    def _zvec_to_embedding(self, data: Dict) -> Dict:
        """Transform Zvec block output to VectorEmbedding."""
        if "result" in data:
            data = data["result"]
        
        return {
            "vector": data.get("embedding", data.get("embeddings", [])),
            "dimension": data.get("dimension", len(data.get("embedding", []))),
            "text": data.get("text", ""),
            "id": data.get("id", ""),
            "metadata": data.get("metadata", {})
        }
    
    def _voice_to_audio(self, data: Dict) -> Dict:
        """Transform Voice block output to AudioContent."""
        if "result" in data:
            data = data["result"]
        
        return {
            "audio_data": data.get("audio_data", data.get("audio_url", "")),
            "format": data.get("format", "mp3"),
            "duration": data.get("duration", 0),
            "text": data.get("text", data.get("transcript", "")),
            "metadata": data.get("metadata", {})
        }
    
    def _translate_to_result(self, data: Dict) -> Dict:
        """Transform Translate block output to TranslationResult."""
        if "result" in data:
            data = data["result"]
        
        return {
            "original_text": data.get("original_text", data.get("source_text", "")),
            "translated_text": data.get("translated_text", "") or data.get("translation", ""),
            "source_language": data.get("source_language", data.get("source_lang", "auto")),
            "target_language": data.get("target_language", data.get("target_lang", "")),
            "metadata": data.get("metadata", {})
        }
    
    def _code_to_result(self, data: Dict) -> Dict:
        """Transform Code block output to CodeResult."""
        if "result" in data:
            data = data["result"]
        
        return {
            "code": data.get("code", ""),
            "language": data.get("language", ""),
            "output": data.get("output", ""),
            "error": data.get("error", ""),
            "analysis": data.get("analysis", data.get("review", "")),
            "metadata": data.get("metadata", {})
        }
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def register(self, source_block: str, target_type: str, transformer: Callable) -> None:
        """
        Register a transformer function.
        
        Args:
            source_block: Block name (e.g., "pdf", "ocr", "chat")
            target_type: Target type name (e.g., "TextContent", "ImageContent")
            transformer: Function that takes data dict and returns transformed dict
        """
        if source_block not in self._transformers:
            self._transformers[source_block] = {}
        self._transformers[source_block][target_type] = transformer
    
    def can_transform(self, source_block: str, target_type: str) -> bool:
        """Check if transformation is available."""
        return (
            source_block in self._transformers and 
            target_type in self._transformers[source_block]
        )
    
    def transform(self, data: Any, target_type: str, source_block: str = None) -> Dict[str, Any]:
        """
        Transform data to target type.
        
        Args:
            data: Input data (can be raw block output or wrapped result)
            target_type: Target type name (e.g., "TextContent")
            source_block: Optional source block hint for selecting transformer
            
        Returns:
            Transformed data matching target type schema
        """
        # If data is None or empty, return empty target type
        if data is None:
            return self._empty_of_type(target_type)
        
        # Extract data from UniversalBlock result wrapper if present
        if isinstance(data, dict) and "result" in data:
            inner_data = data["result"]
        else:
            inner_data = data
        
        # Try to infer source block from data if not provided
        if source_block is None and isinstance(inner_data, dict):
            source_block = self._infer_source_block(inner_data)
        
        # Try specific transformer
        if source_block and self.can_transform(source_block, target_type):
            transformer = self._transformers[source_block][target_type]
            return transformer(data)
        
        # Try generic transformation based on target type
        generic_result = self._generic_transform(inner_data, target_type)
        if generic_result:
            return generic_result
        
        # Return best-effort result
        return self._best_effort_transform(inner_data, target_type)
    
    def _infer_source_block(self, data: Dict) -> Optional[str]:
        """Infer source block from data content."""
        # Check for block-specific fields
        if "pages" in data and "filename" in data:
            return "pdf"
        if "confidence" in data and "word_count" in data:
            return "ocr"
        if "model" in data and "provider" in data:
            return "chat"
        if "embedding" in data or "embeddings" in data:
            return "vector_search"
        if "results" in data and "query" in data:
            return "search"
        if "translated_text" in data:
            return "translate"
        if "file_id" in data or "file_path" in data:
            return "google_drive"
        return None
    
    def _generic_transform(self, data: Any, target_type: str) -> Optional[Dict]:
        """Try generic transformation based on target type."""
        if target_type == "TextContent":
            return self._to_text_content(data)
        elif target_type == "ChatMessage":
            return self._to_chat_message(data)
        elif target_type == "SearchResult":
            return self._to_search_result(data)
        return None
    
    def _best_effort_transform(self, data: Any, target_type: str) -> Dict:
        """Best-effort transformation when no specific transformer exists."""
        if target_type == "TextContent":
            return {
                "text": str(data) if not isinstance(data, dict) else str(data.get("text", data)),
                "source": "unknown",
                "metadata": {"original": data}
            }
        elif target_type == "ChatMessage":
            import time
            return {
                "role": "assistant",
                "content": str(data) if not isinstance(data, dict) else str(data.get("text", data)),
                "timestamp": str(int(time.time())),
                "metadata": {}
            }
        else:
            # Return data as-is for unknown types
            return data if isinstance(data, dict) else {"data": data}
    
    def _empty_of_type(self, target_type: str) -> Dict:
        """Return empty structure for a type."""
        if target_type == "TextContent":
            return {"text": "", "source": "", "metadata": {}}
        elif target_type == "ChatMessage":
            return {"role": "", "content": "", "timestamp": "", "metadata": {}}
        elif target_type == "SearchResult":
            return {"query": "", "results": [], "total_found": 0, "source": "", "metadata": {}}
        return {}
    
    def _to_text_content(self, data: Any) -> Optional[Dict]:
        """Generic transform to TextContent."""
        if isinstance(data, str):
            return {"text": data, "source": "string", "metadata": {}}
        elif isinstance(data, dict):
            # Try common text field names
            text = (
                data.get("text") or 
                data.get("content") or 
                data.get("message") or 
                data.get("body", "")
            )
            if text:
                return {
                    "text": text,
                    "source": "unknown",
                    "metadata": {k: v for k, v in data.items() if k != "text"}
                }
        return None
    
    def _to_chat_message(self, data: Any) -> Optional[Dict]:
        """Generic transform to ChatMessage."""
        import time
        if isinstance(data, str):
            return {
                "role": "assistant",
                "content": data,
                "timestamp": str(int(time.time())),
                "metadata": {}
            }
        elif isinstance(data, dict):
            content = data.get("text") or data.get("content") or str(data)
            return {
                "role": data.get("role", "assistant"),
                "content": content,
                "timestamp": data.get("timestamp", str(int(time.time()))),
                "metadata": {k: v for k, v in data.items() if k not in ["text", "content", "role", "timestamp"]}
            }
        return None
    
    def _to_search_result(self, data: Any) -> Optional[Dict]:
        """Generic transform to SearchResult."""
        if isinstance(data, dict):
            if "results" in data or "items" in data:
                return {
                    "query": data.get("query", ""),
                    "results": data.get("results") or data.get("items", []),
                    "total_found": data.get("total_found", data.get("total", 0)),
                    "source": data.get("source", "unknown"),
                    "metadata": {}
                }
        return None
    
    def list_transformers(self) -> Dict[str, List[str]]:
        """List all available transformers."""
        return {
            block: list(types.keys()) 
            for block, types in self._transformers.items()
        }


# Global transformer instance
transformer = DataTransformer()


def get_transformer() -> DataTransformer:
    """Get the global DataTransformer instance."""
    return transformer


def transform(data: Any, target_type: str, source_block: str = None) -> Dict[str, Any]:
    """
    Convenience function to transform data to target type.
    
    Example:
        pdf_result = await pdf_block.execute("/path/to.pdf", {})
        text_content = transform(pdf_result, "TextContent")
        # Now pass text_content to chat block
        chat_result = await chat_block.execute(text_content["text"], {})
    """
    return transformer.transform(data, target_type, source_block)


# Export
__all__ = [
    "DataTransformer",
    "transformer",
    "get_transformer",
    "transform",
]
