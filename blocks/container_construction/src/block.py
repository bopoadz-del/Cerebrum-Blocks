"""Construction Container - Construction domain container

Contains: BIM, PDF, OCR, Storage, Queue, Workflow
Layer 3 - Domain specific for construction
"""

from blocks.container.src.block import ContainerBlock


class ConstructionContainer(ContainerBlock):
    """Construction tools: BIM, PDF, OCR, Storage, Queue, Workflow"""
    name = "container_construction"
    version = "1.0.0"
    requires = ["event_bus", "container_infrastructure", "bim", "pdf", "ocr", "storage", "queue", "workflow"]
    layer = 3
    tags = ["domain", "construction", "bim", "container"]
    
    default_config = {
        "container_type": "construction",
        "isolation_level": "soft",
        "modules": ["bim", "pdf", "ocr", "storage", "queue", "workflow"],
        "auto_initialize_modules": True,
        "max_file_size": 100 * 1024 * 1024  # 100MB for CAD files
    }
    
    async def initialize(self) -> bool:
        """Initialize construction container with large file support"""
        print("🏗️  Construction Container initializing...")
        print("   Construction layer: BIM, PDF, OCR, Storage, Queue, Workflow")
        print(f"   Max file size: {self.config['max_file_size'] / 1024 / 1024:.0f}MB")
        
        # Initialize parent
        await super().initialize()
        
        # Load all construction modules
        if self.config.get("auto_initialize_modules"):
            for module_name in self.config["modules"]:
                try:
                    class_name = f"{module_name.title().replace('_', '')}Block"
                    if module_name == "bim":
                        class_name = "BIMBlock"
                    elif module_name == "ocr":
                        class_name = "OCRBlock"
                    elif module_name == "pdf":
                        class_name = "PDFBlock"
                        
                    result = await self.execute({
                        "action": "load_module",
                        "module_name": module_name,
                        "module_class": f"blocks.{module_name}.src.block.{class_name}",
                        "config": self._get_module_config(module_name)
                    })
                    
                    if result.get("error"):
                        print(f"   ⚠️  Failed to load {module_name}: {result['error']}")
                    else:
                        print(f"   ✓ Loaded: {module_name}")
                        
                except Exception as e:
                    print(f"   ⚠️  Error loading {module_name}: {e}")
                    
        print(f"   ✓ Construction Container ready with {len(self.modules)} modules")
        return True
        
    def _get_module_config(self, module_name: str) -> dict:
        """Get construction-specific configuration"""
        max_size = self.config["max_file_size"]
        configs = {
            "bim": {
                "max_file_size": max_size,
                "supported_formats": [".ifc", ".rvt", ".dwg"],
                "extract_metadata": True
            },
            "pdf": {
                "max_file_size": max_size,
                "ocr_enabled": True,
                "extract_tables": True
            },
            "ocr": {
                "languages": ["eng"],
                "enhance_images": True
            },
            "storage": {
                "max_file_size": max_size,
                "allowed_types": ["application/pdf", "image/*", "model/*"]
            },
            "queue": {
                "max_retries": 3,
                "priority_levels": 5
            },
            "workflow": {
                "max_steps": 50,
                "timeout_seconds": 3600
            }
        }
        return configs.get(module_name, {"max_file_size": max_size})
        
    async def process_drawing(self, file_id: str, file_type: str) -> dict:
        """Process a construction drawing (PDF or CAD)"""
        if file_type.lower() in [".pdf"]:
            # Process PDF
            ocr_result = await self.execute({
                "action": "route_to_module",
                "module": "ocr",
                "payload": {
                    "action": "extract",
                    "file_id": file_id
                }
            })
            
            pdf_result = await self.execute({
                "action": "route_to_module",
                "module": "pdf",
                "payload": {
                    "action": "extract_text",
                    "file_id": file_id
                }
            })
            
            return {
                "ocr_text": ocr_result.get("text"),
                "pdf_text": pdf_result.get("text"),
                "combined": True
            }
            
        elif file_type.lower() in [".ifc", ".rvt", ".dwg"]:
            # Process BIM model
            return await self.execute({
                "action": "route_to_module",
                "module": "bim",
                "payload": {
                    "action": "parse",
                    "file_id": file_id
                }
            })
            
        return {"error": f"Unsupported file type: {file_type}"}
