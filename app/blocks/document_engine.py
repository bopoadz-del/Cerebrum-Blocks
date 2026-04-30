"""Document Engine Block — Platform wrapper for Parse → Reason → Map pipeline.

Exposes the document_engine block to the Cerebrum platform via:
  POST /execute { "block": "document_engine", "input": { "pdf_path": "..." } }
"""

import os
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class DocumentEngineBlock(UniversalBlock):
    """Technical document reasoning engine.

    Ingests PDF / DOCX / XLSX, runs 8 semantic reasoning pipelines,
    and outputs structured YAML/JSON consumable by schedule_engine,
    cost_engine, and risk_engine downstream blocks.
    """

    name = "document_engine"
    version = "1.0.0"
    description = "Parse → Reason → Map pipeline for technical document intelligence"
    layer = 3
    tags = ["domain", "construction", "documents", "reasoning", "scheduling"]
    requires = ["pdf"]

    default_config = {
        "extract_tables": True,
        "extract_glossary": True,
        "output_format": "yaml",
    }

    ui_schema = {
        "input": {
            "type": "files",
            "accept": [".pdf", ".docx", ".xlsx"],
            "placeholder": "Upload BOD, RFP, or spec documents...",
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "glossary", "type": "list", "label": "Glossary Terms"},
                {"name": "requirements", "type": "list", "label": "Requirements"},
                {"name": "constraints", "type": "list", "label": "Constraints"},
                {"name": "schedule_targets", "type": "list", "label": "Schedule Targets"},
                {"name": "equipment_specs", "type": "list", "label": "Equipment Specs"},
                {"name": "risks", "type": "list", "label": "Risks"},
                {"name": "downstream", "type": "object", "label": "Downstream Feed"},
            ],
        },
        "quick_actions": [
            {"icon": "📄", "label": "Analyze BOD", "prompt": "Extract glossary, constraints, and equipment lead times from Basis of Design"},
            {"icon": "📋", "label": "Analyze RFP", "prompt": "Extract requirements, schedule targets, and risks from RFP"},
            {"icon": "📊", "label": "Schedule Feed", "prompt": "Generate procurement activities and milestones for schedule_engine"},
            {"icon": "⚠️", "label": "Risk Register", "prompt": "Extract all risks and output risk_engine feed"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Main entry point — run the 3-layer pipeline."""
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}

        file_paths = {
            "pdf": data.get("pdf_path") or data.get("pdf") or params.get("pdf_path"),
            "docx": data.get("docx_path") or data.get("docx") or params.get("docx_path"),
            "xlsx": data.get("xlsx_path") or data.get("xlsx") or params.get("xlsx_path"),
        }

        if not any(file_paths.values()):
            return {"status": "error", "error": "No input files provided (pdf/docx/xlsx)"}

        try:
            from blocks.document_engine.main import parse_all
            from blocks.document_engine.reasoner import DocumentReasoner
            from blocks.document_engine.mapper import DocumentMapper
            import yaml

            block_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(block_dir, "blocks", "document_engine", "config.yaml")

            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    full_config = yaml.safe_load(f)
                config = full_config.get("document_engine", full_config)
            else:
                config = {}

            # Layer 1: Parse
            documents = parse_all(file_paths, config)

            # Layer 2: Reason
            reasoner = DocumentReasoner(config)
            reasoned = reasoner.reason(documents)

            # Layer 3: Map
            mapper = DocumentMapper(config)
            structured = mapper.map_to_structured(reasoned)

            result = structured.to_dict()
            result["status"] = "success"
            result["documents_parsed"] = len(documents)
            return result

        except Exception as e:
            return {"status": "error", "error": f"Document engine pipeline failed: {str(e)}"}
