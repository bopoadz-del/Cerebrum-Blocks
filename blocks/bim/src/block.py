from blocks.base import LegoBlock
from typing import Dict, Any, List, Optional
import os
import json
from datetime import datetime

class BIMBlock(LegoBlock):
    """
    BIM File Processor - Handles drawings, models, specs from Google Drive/Local
    NO 3D geometry engine - file metadata + text extraction for PoC
    """
    
    name = "bim"
    version = "1.0.0"
    requires = ["config", "storage", "vector"]
    
    SUPPORTED_FORMATS = {
        ".ifc": "bim_model",
        ".dwg": "cad_drawing", 
        ".pdf": "drawing_pdf",
        ".rvt": "revit_model",
        ".nwd": "navisworks",
        ".xlsx": "schedule",
        ".csv": "data_export"
    }
    
    def __init__(self, hal_block, config: Dict[str, Any]):
        super().__init__(hal_block, config)
        self.storage_block = None  # Wired by assembler
        self.vector_block = None
        self.pdf_block = None
        self.ocr_block = None
        
        # Project file index
        self.projects = {}  # project_id -> {files: [], metadata: {}}
        
        # Google Drive integration
        self.drive_connected = False
    
    async def initialize(self):
        """Init BIM file processor"""
        print(f"📐 BIM File Processor ready")
        print(f"   Supports: {list(self.SUPPORTED_FORMATS.keys())}")
        return True
    
    async def execute(self, input_data: Dict) -> Dict:
        """BIM file operations"""
        action = input_data.get("action")
        
        if action == "index_folder":
            return await self._index_drive_folder(input_data)
        elif action == "process_file":
            return await self._process_file(input_data)
        elif action == "search_drawings":
            return await self._search_drawings(input_data)
        elif action == "get_metadata":
            return await self._get_file_metadata(input_data)
        elif action == "compare_versions":
            return await self._compare_versions(input_data)
        elif action == "extract_schedule":
            return await self._extract_schedule(input_data)
        
        return {"error": f"Unknown action: {action}"}
    
    async def _index_drive_folder(self, data: Dict) -> Dict:
        """Index all BIM files from Google Drive or Local folder"""
        project_id = data.get("project_id")
        folder_path = data.get("folder_path")  # "gdrive:/Projects/Diriyah" or "/data/projects/diriyah"
        drive_type = "gdrive" if folder_path.startswith("gdrive:") else "local"
        
        if not self.storage_block:
            return {"error": "Storage block not connected"}
        
        # List files in folder
        files_result = await self.storage_block.execute({
            "action": "list",
            "drive": drive_type,
            "path": folder_path.replace("gdrive:", "") if drive_type == "gdrive" else folder_path
        })
        
        if "error" in files_result:
            return files_result
        
        # Filter BIM-related files
        bim_files = []
        for file in files_result.get("files", []):
            ext = os.path.splitext(file["name"])[1].lower()
            if ext in self.SUPPORTED_FORMATS:
                bim_files.append({
                    "name": file["name"],
                    "type": self.SUPPORTED_FORMATS[ext],
                    "path": f"{folder_path}/{file['name']}",
                    "drive": drive_type,
                    "size": file.get("size", 0),
                    "modified": file.get("modified", 0)
                })
        
        # Process each file for metadata
        processed = []
        for bim_file in bim_files:
            meta = await self._extract_metadata(bim_file)
            processed.append({**bim_file, **meta})
            
            # Index in vector DB for searchability
            if self.vector_block:
                await self.vector_block.execute({
                    "action": "add",
                    "text": f"{bim_file['name']}: {meta.get('description', 'BIM file')}",
                    "metadata": {**bim_file, "project": project_id}
                })
        
        # Store project index
        self.projects[project_id] = {
            "folder": folder_path,
            "files": processed,
            "indexed_at": datetime.now().isoformat(),
            "total_files": len(processed)
        }
        
        return {
            "project_id": project_id,
            "indexed": len(processed),
            "by_type": self._count_by_type(processed),
            "drive": drive_type
        }
    
    async def _extract_metadata(self, file_info: Dict) -> Dict:
        """Extract metadata from BIM file (without heavy parsing)"""
        file_type = file_info["type"]
        
        if file_type == "drawing_pdf":
            # Use PDF block to extract text
            if self.pdf_block:
                pdf_result = await self.pdf_block.execute({
                    "action": "extract",
                    "path": file_info["path"],
                    "drive": file_info["drive"]
                })
                return {
                    "description": pdf_result.get("text", "")[:200],
                    "sheets": pdf_result.get("pages", 0),
                    "extracted": True
                }
        
        elif file_type == "bim_model":
            # IFC metadata extraction (lightweight)
            return {
                "description": "BIM Model file",
                "schema": "IFC2X3",  # Would detect from header
                "entities": 0,  # Would count if parsed
                "extracted": False  # Heavy parsing deferred
            }
        
        elif file_type == "cad_drawing":
            return {
                "description": "AutoCAD Drawing",
                "version": "Unknown",
                "extracted": False
            }
        
        return {"description": f"{file_type} file", "extracted": False}
    
    async def _process_file(self, data: Dict) -> Dict:
        """Deep process a specific file (OCR, text extraction)"""
        project_id = data.get("project_id")
        filename = data.get("filename")
        
        # Find file in project
        project = self.projects.get(project_id, {})
        file_info = next((f for f in project.get("files", []) if f["name"] == filename), None)
        
        if not file_info:
            return {"error": f"File {filename} not found in project {project_id}"}
        
        # Read file content
        content_result = await self.storage_block.execute({
            "action": "retrieve",
            "file_id": file_info["path"]
        })
        
        if "error" in content_result:
            return content_result
        
        # Process based on type
        processing_result = {}
        
        if file_info["type"] == "drawing_pdf":
            # OCR for drawings
            if self.ocr_block:
                ocr_result = await self.ocr_block.execute({
                    "action": "extract",
                    "image_data": content_result.get("content"),
                    "engine": "advanced"
                })
                processing_result = {
                    "text_extracted": ocr_result.get("text", ""),
                    "annotations_found": ocr_result.get("annotations", []),
                    "confidence": ocr_result.get("confidence", 0)
                }
        
        # Update file record
        file_info["processed"] = True
        file_info["processing_result"] = processing_result
        
        # Re-index with processed content
        if self.vector_block and processing_result.get("text_extracted"):
            await self.vector_block.execute({
                "action": "add",
                "text": processing_result["text_extracted"],
                "metadata": {"type": "extracted_text", "source": filename, "project": project_id}
            })
        
        return {
            "file": filename,
            "processed": True,
            "result": processing_result
        }
    
    async def _search_drawings(self, data: Dict) -> Dict:
        """Semantic search across all project drawings"""
        project_id = data.get("project_id")
        query = data.get("query")  # e.g., "foundation slab detail"
        
        if not self.vector_block:
            return {"error": "Vector block not connected"}
        
        # Search vector DB
        results = await self.vector_block.execute({
            "action": "search",
            "query": f"BIM drawing {query}",
            "top_k": 10
        })
        
        # Filter to this project
        project_results = [
            r for r in results.get("results", [])
            if project_id in str(r.get("metadata", {}).get("project", ""))
        ]
        
        return {
            "query": query,
            "drawings_found": len(project_results),
            "results": project_results,
            "suggested_drawings": [r.get("metadata", {}).get("name") for r in project_results[:3]]
        }
    
    async def _get_file_metadata(self, data: Dict) -> Dict:
        """Get metadata for specific file"""
        project_id = data.get("project_id")
        filename = data.get("filename")
        
        project = self.projects.get(project_id, {})
        file_info = next((f for f in project.get("files", []) if f["name"] == filename), None)
        
        if not file_info:
            return {"error": "File not found"}
        
        return {
            "metadata": file_info,
            "project": project_id,
            "available_for_processing": not file_info.get("processed", False)
        }
    
    async def _compare_versions(self, data: Dict) -> Dict:
        """Compare two versions of same drawing"""
        project_id = data.get("project_id")
        filename = data.get("filename")
        version_a = data.get("version_a")
        version_b = data.get("version_b")
        
        # Placeholder - would extract and compare
        return {
            "comparison": "placeholder",
            "changes_detected": 0,
            "method": "hash_comparison"
        }
    
    async def _extract_schedule(self, data: Dict) -> Dict:
        """Extract construction schedule from Excel/CSV"""
        project_id = data.get("project_id")
        schedule_file = data.get("file")  # "schedule.xlsx"
        
        # Would parse Excel/CSV
        # Return activities with BIM element links
        
        return {
            "activities": [
                {"id": "A101", "name": "Foundation", "start": "2026-04-01", "elements": ["slab_01"]}
            ],
            "file": schedule_file
        }
    
    def _count_by_type(self, files: List[Dict]) -> Dict:
        """Count files by BIM type"""
        counts = {}
        for f in files:
            t = f["type"]
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    def health(self) -> Dict:
        h = super().health()
        h["projects_indexed"] = len(self.projects)
        h["files_tracked"] = sum(p.get("total_files", 0) for p in self.projects.values())
        h["drive_connected"] = self.storage_block is not None
        return h
