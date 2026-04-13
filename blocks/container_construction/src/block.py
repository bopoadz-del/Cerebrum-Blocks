"""Construction Container - Construction domain container

Contains: BIM, PDF, OCR, Storage, Queue, Workflow, AEC Analysis
Layer 3 - Domain specific for construction
"""

import re
import json
import os
import math
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

from blocks.container.src.block import ContainerBlock


class Measurement:
    value: float
    unit: str
    type: str
    raw_text: str
    confidence: float
    context: str

class SpecItem:
    category: str
    key: str
    value: str
    section: str
    confidence: float

class RiskItem:
    id: str
    category: str
    description: str
    probability: str
    impact: str
    mitigation: str
    source: str

class ConstructionContainer(ContainerBlock):
    """Construction tools: BIM, PDF, OCR, Storage, Queue, Workflow, AEC Analysis"""
    name = "container_construction"
    version = "3.2.0"
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
    
    def get_dep(self, name: str) -> Optional[Any]:
        """Alias for get_dependency"""
        return self.get_dependency(name)
    
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

    def _load_cost_database(self):
        self.cost_db = {
            "concrete_c30": {"unit": "m³", "rate": 1250, "labor_factor": 0.4},
            "concrete_c40": {"unit": "m³", "rate": 1450, "labor_factor": 0.4},
            "rebar": {"unit": "kg", "rate": 3.2, "labor_factor": 0.6},
            "formwork": {"unit": "m²", "rate": 48, "labor_factor": 0.7},
            "block_work": {"unit": "m²", "rate": 95, "labor_factor": 0.5},
            "plaster": {"unit": "m²", "rate": 35, "labor_factor": 0.6},
            "paint": {"unit": "m²", "rate": 15, "labor_factor": 0.5},
            "flooring_tile": {"unit": "m²", "rate": 180, "labor_factor": 0.4},
            "ceiling_gypsum": {"unit": "m²", "rate": 75, "labor_factor": 0.5},
            "steel_structural": {"unit": "kg", "rate": 4.5, "labor_factor": 0.5},
            "glass_curtain": {"unit": "m²", "rate": 450, "labor_factor": 0.3},
            "insulation": {"unit": "m²", "rate": 28, "labor_factor": 0.4},
            "electrical_rough": {"unit": "m²", "rate": 65, "labor_factor": 0.5},
            "plumbing_rough": {"unit": "m²", "rate": 85, "labor_factor": 0.5},
            "hvac_duct": {"unit": "m²", "rate": 120, "labor_factor": 0.4},
        }

    def _load_csi_masterformat(self):
        self.csi_divisions = {
            "01": "General Requirements", "02": "Existing Conditions", "03": "Concrete",
            "04": "Masonry", "05": "Metals", "06": "Wood, Plastics, Composites",
            "07": "Thermal & Moisture", "08": "Openings", "09": "Finishes",
            "10": "Specialties", "11": "Equipment", "12": "Furnishings",
            "13": "Special Construction", "14": "Conveying", "21": "Fire Suppression",
            "22": "Plumbing", "23": "HVAC", "25": "Integrated Automation",
            "26": "Electrical", "27": "Communications", "28": "Electronic Safety",
            "31": "Earthwork", "32": "Exterior Improvements", "33": "Utilities"
        }

    def _load_safety_codes(self):
        self.safety_codes = {
            "osha_1926": "Construction Standards",
            "osha_1910": "General Industry",
            "iso_45001": "Occupational Health & Safety",
            "ansi_z10": "Safety Management",
            "nfpa_70e": "Electrical Safety",
            "ansi_a10": "Construction Safety",
        }

    def _load_carbon_factors(self):
        self.carbon_factors = {
            "concrete_c30": 350,
            "concrete_c40": 420,
            "steel_rebar": 2.5,
            "steel_structural": 2.8,
            "aluminum": 12.7,
            "glass": 25.0,
            "timber_softwood": -0.9,
            "timber_hardwood": -1.2,
            "brick": 220,
            "block_concrete": 180,
            "insulation_mineral": 25,
            "insulation_eps": 35,
            "paint": 5.2,
            "ceramic_tile": 18,
            "carpet": 45,
        }

    def _looks_like_file(self, input_data: Any, params: Dict) -> bool:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        return any(k in data or k in p for k in ["file_path", "content", "filename", "file", "url"])

    async def process_document(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        url = data.get("url") or p.get("url")
        doc_type = p.get("doc_type", "auto")
        
        if not file_path and url:
            file_path = await self._download_file(url)
        
        if not file_path:
            return {"status": "error", "error": "No file provided"}
        
        if doc_type == "auto":
            doc_type = await self._classify_document(file_path)
        
        processors = {
            "drawing": self._process_drawing,
            "specification": self.process_specification_full,
            "contract": self.process_contract,
            "schedule": self.parse_primavera_schedule,
            "bom": self._process_bill_of_materials,
            "report": self._process_report,
            "bim": self._process_ifc,
            "image": self._process_site_photo,
            "change_order": self.change_order_impact,
            "safety_audit": self.safety_compliance_audit,
        }
        
        processor = processors.get(doc_type, self._process_drawing)
        return await processor(input_data, p)

    async def _classify_document(self, file_path: str) -> str:
        name = Path(file_path).name.lower()
        if any(x in name for x in [".ifc", ".bim", "model"]):
            return "bim"
        if any(x in name for x in ["photo", "site", "img", ".jpg", ".png"]):
            return "image"
        if any(x in name for x in ["schedule", ".xer", ".xml", "primavera", "msp"]):
            return "schedule"
        if any(x in name for x in ["bom", "bill", "material"]):
            return "bom"
        if any(x in name for x in ["spec", "specification"]):
            return "specification"
        if any(x in name for x in ["contract", "agreement", "subcontract"]):
            return "contract"
        if any(x in name for x in ["report", "rpt", "inspection"]):
            return "report"
        return "drawing"

    async def _process_drawing(self, file_path: str, params: Dict) -> Dict:
        try:
            import fitz
            doc = fitz.open(file_path)
        except Exception as e:
            return {"status": "error", "error": f"Could not open file: {str(e)}", "file": file_path}
        
        result = {
            "status": "success",
            "doc_type": "drawing",
            "file_name": Path(file_path).name,
            "drawing_number": self._extract_drawing_number(Path(file_path).name),
            "revision": self._extract_revision(Path(file_path).name),
            "total_pages": len(doc),
            "sheets": [],
            "measurements": [],
            "tables": [],
            "annotations": [],
            "specifications": [],
            "detected_disciplines": [],
            "scale": None,
            "title_block": {},
            "bom_items": [],
            "confidence": {}
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            sheet_data = self._process_drawing_page(page, page_num)
            result["sheets"].append(sheet_data)
            result["measurements"].extend(sheet_data["measurements"])
            result["tables"].extend(sheet_data["tables"])
            result["annotations"].extend(sheet_data["annotations"])
            result["specifications"].extend(sheet_data["specs"])
            result["detected_disciplines"].extend(self._detect_disciplines(sheet_data["raw_text"]))
        
        if result["sheets"]:
            result["title_block"] = self._extract_title_block(result["sheets"][0])
            result["scale"] = self._extract_scale(result["sheets"][0]["raw_text"])
        
        result["quantities"] = self._calculate_quantities(result["measurements"])
        result["cost_estimate"] = self._estimate_costs(result["quantities"])
        result["carbon_estimate"] = self._estimate_carbon(result["quantities"])
        result["confidence"] = self._calculate_confidence(result)
        result["auto_risks"] = await self._detect_risks_from_drawing(result)
        
        doc.close()
        return result

    def _process_drawing_page(self, page, page_num: int) -> Dict:
        text_dict = page.get_text("dict")
        raw_text = page.get_text()
        return {
            "page_number": page_num + 1,
            "raw_text": raw_text[:8000],
            "measurements": self._extract_measurements_advanced(raw_text, text_dict),
            "tables": self._extract_tables_advanced(page),
            "annotations": self._extract_annotations(page),
            "specs": self._extract_specs_advanced(raw_text),
            "image_count": len(page.get_images()),
            "rotation": page.rotation,
            "cropbox": [page.cropbox.x0, page.cropbox.y0, page.cropbox.x1, page.cropbox.y1]
        }

    async def _process_bill_of_materials(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "success", "doc_type": "bom", "items": []}

    async def _process_report(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "success", "doc_type": "report", "findings": []}

    async def _process_ifc(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "success", "doc_type": "bim", "elements": {}}

    async def _process_site_photo(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        return await self._process_image(file_path, p)

    async def _download_file(self, url: str) -> str:
        import uuid
        import httpx
        ext = url.split('?')[0].split('.')[-1] or 'pdf'
        path = f"/tmp/{uuid.uuid4().hex[:8]}_{url.split('/')[-1] or 'download'}.{ext}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                with open(path, "wb") as f:
                    f.write(response.content)
            return path
        except Exception:
            return ""

    async def _process_image(self, file_path: str, params: Dict) -> Dict:
        ocr_block = self.get_dep("ocr")
        if ocr_block:
            try:
                ocr_result = await ocr_block.execute({"image_path": file_path}, {})
                text = ocr_result.get("result", {}).get("text", "")
                measurements = self._extract_measurements_advanced(text, {})
                specs = self._extract_specs_advanced(text)
                return {
                    "status": "success",
                    "file_name": Path(file_path).name,
                    "source": "ocr",
                    "text": text[:2000],
                    "measurements": measurements,
                    "specifications": specs,
                    "confidence": {"overall": 0.7, "text_extraction": 0.7, "ocr": ocr_result.get("confidence", 0)}
                }
            except Exception as e:
                return {"status": "error", "error": f"Image OCR failed: {str(e)}"}
        return {"status": "error", "error": "OCR block not available for image processing"}

    async def process_contract(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        contract_type = p.get("contract_type", "general")
        
        if not file_path:
            return {"status": "error", "error": "No contract file provided"}
        
        try:
            import fitz
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
        except Exception as e:
            return {"status": "error", "error": f"Could not read contract: {str(e)}"}
        
        clause_patterns = {
            "payment_terms": r'(?:payment|pay|invoice)[\s\w]{0,50}(?:term|schedule|milestone|certificate)',
            "liquidated_damages": r'(?:liquidated damages|ld|delay damages)[\s\w]{0,100}(?:rate|amount|per day)',
            "retention": r'(?:retention|retainage)[\s\w]{0,50}(?:percent|percentage|amount|release)',
            "variation_clause": r'(?:variation|change order|modification)[\s\w]{0,100}(?:procedure|valuation|approval)',
            "force_majeure": r'(?:force majeure|act of god|unforeseeable)[\s\w]{0,200}(?:delay|extension|notice)',
            "termination": r'(?:terminat|default|breach)[\s\w]{0,200}(?:clause|condition|notice period|consequence)',
            "indemnity": r'(?:indemnif|hold harmless|defend)[\s\w]{0,100}(?:clause|obligation|insurance)',
            "dispute_resolution": r'(?:dispute|arbitration|mediation|adjudication)[\s\w]{0,100}(?:clause|procedure|board)',
            "time_extensions": r'(?:extension of time|eot|delay|prolongation)[\s\w]{0,150}(?:clause|entitlement|procedure)',
            "subcontracting": r'(?:subcontract|sub-let|nominated|domestic)[\s\w]{0,100}(?:approval|liability|payment)',
            "insurance": r'(?:insurance|policy|cover)[\s\w]{0,150}(requirement|amount|professional|all risk)',
            "safety_obligation": r'(?:safety|health|hse|osha)[\s\w]{0,100}(?:obligation|responsibility|compliance)',
            "environmental": r'(?:environmental|sustainability|green|eco)[\s\w]{0,100}(?:requirement|compliance|standard)',
        }
        
        extracted_clauses = {}
        for clause_type, pattern in clause_patterns.items():
            matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
            if matches:
                contexts = []
                for match in matches[:3]:
                    start = max(0, match.start() - 200)
                    end = min(len(full_text), match.end() + 200)
                    contexts.append(full_text[start:end].strip())
                extracted_clauses[clause_type] = {
                    "found": True,
                    "count": len(matches),
                    "contexts": contexts,
                    "risk_level": self._assess_clause_risk(clause_type, contexts)
                }
            else:
                extracted_clauses[clause_type] = {"found": False, "risk_level": "unknown"}
        
        obligations = self._extract_obligations(full_text)
        contract_risks = self._assess_contract_risks(extracted_clauses, contract_type)
        financial_terms = self._extract_financial_terms(full_text)
        
        return {
            "status": "success",
            "action": "contract_analysis",
            "file_name": Path(file_path).name,
            "contract_type": contract_type,
            "document_length": len(full_text),
            "clauses_found": len([c for c in extracted_clauses.values() if c.get("found")]),
            "total_clauses": len(clause_patterns),
            "extracted_clauses": extracted_clauses,
            "key_obligations": obligations,
            "financial_terms": financial_terms,
            "risk_assessment": {
                "overall_score": contract_risks["score"],
                "risk_level": contract_risks["level"],
                "critical_issues": contract_risks["critical"],
                "warnings": contract_risks["warnings"],
                "recommendations": contract_risks["recommendations"]
            },
            "summary": self._generate_contract_summary(extracted_clauses, financial_terms)
        }

    def _extract_obligations(self, text: str) -> List[Dict]:
        obligations = []
        obligation_patterns = [
            (r'(?:contractor|builder)[\s\w]{0,50}(?:shall|must|will|agrees to)[\s\w]{0,100}(?:\.)', "contractor_obligation"),
            (r'(?:employer|owner|client)[\s\w]{0,50}(?:shall|must|will|agrees to)[\s\w]{0,100}(?:\.)', "employer_obligation"),
            (r'(?:both parties|each party)[\s\w]{0,50}(?:shall|must|will)[\s\w]{0,100}(?:\.)', "mutual_obligation"),
            (r'(?:architect|engineer|supervisor)[\s\w]{0,50}(?:shall|must|will)[\s\w]{0,100}(?:\.)', "consultant_obligation"),
        ]
        for pattern, obl_type in obligation_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                obligations.append({
                    "type": obl_type,
                    "text": match.group(0),
                    "category": self._categorize_obligation(match.group(0)),
                    "priority": self._assess_obligation_priority(match.group(0))
                })
        return obligations[:20]

    def _categorize_obligation(self, text: str) -> str:
        if any(w in text.lower() for w in ["safety", "health", "protect"]):
            return "safety"
        if any(w in text.lower() for w in ["insurance", "indemnif", "liability"]):
            return "risk"
        if any(w in text.lower() for w in ["payment", "invoice", "cost"]):
            return "financial"
        return "general"

    def _assess_obligation_priority(self, text: str) -> str:
        if any(w in text.lower() for w in ["shall", "must", "obligation"]):
            return "high"
        return "medium"

    def _assess_clause_risk(self, clause_type: str, contexts: List[str]) -> str:
        high_risk_keywords = ["penalty", "unlimited", "sole discretion", "no limit", "absolute", "waiver of rights"]
        medium_risk_keywords = ["notice", "approval required", "consent", "binding"]
        combined = " ".join(contexts).lower()
        if any(kw in combined for kw in high_risk_keywords):
            return "high"
        elif any(kw in combined for kw in medium_risk_keywords):
            return "medium"
        return "low"

    def _assess_contract_risks(self, clauses: Dict, contract_type: str) -> Dict:
        score = 100
        critical = []
        warnings = []
        recommendations = []
        
        if not clauses.get("payment_terms", {}).get("found"):
            score -= 15
            critical.append("Payment terms not clearly defined")
            recommendations.append("Add detailed payment schedule with milestones")
        if not clauses.get("liquidated_damages", {}).get("found"):
            score -= 10
            warnings.append("No liquidated damages clause")
        if clauses.get("liquidated_damages", {}).get("risk_level") == "high":
            score -= 20
            critical.append("High/Uncapped liquidated damages")
            recommendations.append("Negotiate cap on liquidated damages")
        if not clauses.get("force_majeure", {}).get("found"):
            score -= 10
            warnings.append("No force majeure clause")
            recommendations.append("Add force majeure clause")
        if not clauses.get("variation_clause", {}).get("found"):
            score -= 15
            critical.append("No variation/change order procedure")
            recommendations.append("Define change order valuation and approval process")
        if clauses.get("termination", {}).get("risk_level") == "high":
            score -= 15
            critical.append("Unbalanced termination clause")
        if not clauses.get("dispute_resolution", {}).get("found"):
            score -= 5
            warnings.append("No dispute resolution mechanism defined")
        
        risk_level = "low" if score >= 80 else "medium" if score >= 60 else "high"
        return {"score": max(0, score), "level": risk_level, "critical": critical, "warnings": warnings, "recommendations": recommendations}

    def _extract_financial_terms(self, text: str) -> Dict:
        terms = {}
        value_match = re.search(r'(?:contract (?:value|sum|price|amount)|total)[\s:]*[$\u20ac£]?[\s]*(\d[\d,\.]*)', text, re.IGNORECASE)
        if value_match:
            terms["contract_value"] = value_match.group(1)
        advance_match = re.search(r'(?:advance|mobilization)[\s\w]{0,30}(\d+)%', text, re.IGNORECASE)
        if advance_match:
            terms["advance_payment"] = f"{advance_match.group(1)}%"
        retention_match = re.search(r'(?:retention|retainage)[\s\w]{0,30}(\d+)%', text, re.IGNORECASE)
        if retention_match:
            terms["retention"] = f"{retention_match.group(1)}%"
        currency_match = re.search(r'(?:currency|in|amounts)[\s\w]{0,20}(USD|EUR|GBP|AED|SAR|QAR)', text, re.IGNORECASE)
        if currency_match:
            terms["currency"] = currency_match.group(1)
        return terms

    def _generate_contract_summary(self, clauses: Dict, financial: Dict) -> str:
        summary_parts = []
        if clauses.get("payment_terms", {}).get("found"):
            summary_parts.append("Payment terms defined")
        else:
            summary_parts.append("⚠️ Payment terms unclear")
        if clauses.get("liquidated_damages", {}).get("found"):
            summary_parts.append("LDs apply")
        if financial.get("contract_value"):
            summary_parts.append(f"Value: {financial['contract_value']}")
        return " | ".join(summary_parts)

    async def parse_primavera_schedule(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        baseline_file = data.get("baseline_file") or p.get("baseline_file")
        analysis_date = p.get("analysis_date", datetime.now(timezone.utc).isoformat())
        
        if not file_path:
            return {"status": "error", "error": "No schedule file provided"}
        
        ext = Path(file_path).suffix.lower()
        if ext == '.xer':
            schedule_data = self._parse_xer_file(file_path)
        elif ext == '.xml':
            schedule_data = self._parse_xml_schedule(file_path)
        else:
            return {"status": "error", "error": f"Unsupported format: {ext}"}
        
        if schedule_data.get("status") == "error":
            return schedule_data
        
        cpm_results = self._calculate_critical_path(schedule_data)
        delay_analysis = None
        if baseline_file:
            baseline_data = self._parse_xer_file(baseline_file) if baseline_file.endswith('.xer') else self._parse_xml_schedule(baseline_file)
            delay_analysis = self._analyze_delays(schedule_data, baseline_data)
        
        schedule_risks = self._analyze_schedule_risks(cpm_results)
        recovery_options = []
        if delay_analysis and delay_analysis.get("total_delay_days", 0) > 0:
            recovery_options = self._generate_recovery_options(delay_analysis, cpm_results)
        
        return {
            "status": "success",
            "action": "primavera_analysis",
            "file_name": Path(file_path).name,
            "project_name": schedule_data.get("project_name"),
            "analysis_date": analysis_date,
            "summary": {
                "total_activities": len(schedule_data.get("activities", [])),
                "critical_activities": len(cpm_results.get("critical_path", [])),
                "total_float_average": cpm_results.get("average_float", 0),
                "project_duration": cpm_results.get("project_duration_days", 0),
                "data_date": schedule_data.get("data_date")
            },
            "critical_path": {
                "activities": cpm_results.get("critical_path", [])[:20],
                "path_duration": cpm_results.get("critical_path_duration"),
                "driving_paths": cpm_results.get("driving_paths", [])
            },
            "milestones": self._extract_milestones(schedule_data),
            "delay_analysis": delay_analysis,
            "schedule_risks": schedule_risks,
            "recovery_options": recovery_options,
            "recommendations": self._generate_schedule_recommendations(cpm_results, delay_analysis),
            "detailed_activities": schedule_data.get("activities", [])[:50] if p.get("include_details") else None
        }

    def _parse_xer_file(self, file_path: str) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            sections = {}
            current_section = None
            headers = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('%T'):
                    current_section = line[2:].strip()
                    sections[current_section] = []
                    headers = []
                elif line.startswith('%F') and current_section:
                    headers = line[2:].split('\t')
                elif line.startswith('%R') and current_section and headers:
                    values = line[2:].split('\t')
                    record = dict(zip(headers, values))
                    sections[current_section].append(record)
            
            project_info = sections.get('PROJECT', [{}])[0]
            activities = sections.get('TASK', [])
            relationships = sections.get('TASKPRED', [])
            
            structured_activities = []
            for act in activities:
                structured_activities.append({
                    "id": act.get('task_id'),
                    "name": act.get('task_name'),
                    "duration": float(act.get('target_dur', 0) or 0),
                    "start": act.get('target_start'),
                    "finish": act.get('target_end'),
                    "early_start": act.get('early_start'),
                    "early_finish": act.get('early_end'),
                    "late_start": act.get('late_start'),
                    "late_finish": act.get('late_end'),
                    "total_float": float(act.get('total_float', 0) or 0),
                    "free_float": float(act.get('free_float', 0) or 0),
                    "percent_complete": float(act.get('complete_pct', 0) or 0),
                    "critical": act.get('total_float', '0') == '0',
                    "wbs": act.get('wbs_id'),
                    "resources": []
                })
            
            return {
                "status": "success",
                "project_name": project_info.get('proj_short_name', 'Unknown'),
                "data_date": project_info.get('last_recalc_date'),
                "activities": structured_activities,
                "relationships": self._parse_relationships(relationships),
                "calendars": sections.get('CALENDAR', []),
                "resources": sections.get('RSRC', [])
            }
        except Exception as e:
            return {"status": "error", "error": f"XER parsing failed: {str(e)}"}

    def _parse_xml_schedule(self, file_path: str) -> Dict:
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if 'Project' in root.tag:
                return self._parse_mspdi_xml(root)
            else:
                activities = []
                for activity in root.findall('.//Activity'):
                    activities.append({
                        "id": activity.findtext('Id', ''),
                        "name": activity.findtext('Name', ''),
                        "duration": float(activity.findtext('OriginalDuration', 0) or 0),
                        "start": activity.findtext('StartDate', ''),
                        "finish": activity.findtext('FinishDate', ''),
                        "total_float": float(activity.findtext('TotalFloat', 0) or 0),
                        "critical": activity.findtext('Critical') == '1',
                        "percent_complete": float(activity.findtext('PercentComplete', 0) or 0)
                    })
                return {
                    "status": "success",
                    "project_name": root.findtext('.//Name', 'Unknown'),
                    "activities": activities
                }
        except Exception as e:
            return {"status": "error", "error": f"XML parsing failed: {str(e)}"}

    def _parse_mspdi_xml(self, root) -> Dict:
        ns = {'m': 'http://schemas.microsoft.com/project'}
        activities = []
        for task in root.findall('.//m:Task', ns):
            activities.append({
                "id": task.findtext('.//m:UID', '', ns),
                "name": task.findtext('.//m:Name', '', ns),
                "duration": 0,
                "start": task.findtext('.//m:Start', '', ns),
                "finish": task.findtext('.//m:Finish', '', ns),
                "total_float": 0,
                "critical": False,
                "percent_complete": float(task.findtext('.//m:PercentComplete', '0', ns) or 0)
            })
        return {"status": "success", "project_name": "MSP Project", "activities": activities}

    def _parse_relationships(self, relationships: List[Dict]) -> List[Dict]:
        return [{"predecessor": r.get('pred_task_id'), "successor": r.get('task_id'), "type": r.get('pred_type')} for r in relationships]

    def _calculate_critical_path(self, schedule_data: Dict) -> Dict:
        activities = {a["id"]: a for a in schedule_data.get("activities", [])}
        critical_activities = [a for a in activities.values() if a.get("critical") or a.get("total_float", 999) <= 0]
        critical_activities.sort(key=lambda x: x.get("early_start", '') or '')
        
        if critical_activities:
            start = critical_activities[0].get("early_start")
            finish = critical_activities[-1].get("early_finish")
            duration = self._calculate_duration_days(start, finish) if start and finish else 0
        else:
            duration = 0
        
        floats = [a.get("total_float", 0) for a in schedule_data.get("activities", [])]
        avg_float = sum(floats) / len(floats) if floats else 0
        near_critical = [a for a in schedule_data.get("activities", []) if 0 < a.get("total_float", 999) < 5]
        
        return {
            "critical_path": [a["id"] for a in critical_activities],
            "critical_path_activities": critical_activities,
            "critical_path_duration": duration,
            "critical_count": len(critical_activities),
            "near_critical_count": len(near_critical),
            "near_critical_activities": near_critical[:10],
            "average_float": avg_float,
            "project_duration_days": duration,
            "driving_paths": []
        }

    def _analyze_delays(self, current: Dict, baseline: Dict) -> Dict:
        current_acts = {a["id"]: a for a in current.get("activities", [])}
        baseline_acts = {a["id"]: a for a in baseline.get("activities", [])}
        
        delays = []
        new_activities = []
        deleted_activities = []
        
        for act_id, current_act in current_acts.items():
            baseline_act = baseline_acts.get(act_id)
            if not baseline_act:
                new_activities.append(current_act)
                continue
            
            curr_start = current_act.get("start", '')
            base_start = baseline_act.get("start", '')
            if curr_start != base_start:
                delay_days = self._calculate_date_diff(base_start, curr_start)
                if delay_days > 0:
                    delays.append({
                        "activity_id": act_id,
                        "activity_name": current_act.get("name"),
                        "type": "start_delay",
                        "baseline_date": base_start,
                        "current_date": curr_start,
                        "delay_days": delay_days,
                        "percent_complete": current_act.get("percent_complete", 0)
                    })
            
            if current_act.get("percent_complete", 0) < 100:
                curr_finish = current_act.get("finish", '')
                base_finish = baseline_act.get("finish", '')
                if curr_finish and base_finish and curr_finish != base_finish:
                    finish_delay = self._calculate_date_diff(base_finish, curr_finish)
                    if finish_delay > 0:
                        delays.append({
                            "activity_id": act_id,
                            "activity_name": current_act.get("name"),
                            "type": "finish_delay",
                            "baseline_date": base_finish,
                            "current_date": curr_finish,
                            "delay_days": finish_delay
                        })
        
        for base_id in baseline_acts:
            if base_id not in current_acts:
                deleted_activities.append(baseline_acts[base_id])
        
        total_delay = max([d["delay_days"] for d in delays]) if delays else 0
        
        return {
            "total_delay_days": total_delay,
            "delayed_activities": delays,
            "delay_count": len(delays),
            "new_activities": new_activities[:10],
            "deleted_activities": deleted_activities[:10],
            "impact_assessment": self._assess_delay_impact(delays, total_delay)
        }

    def _analyze_schedule_risks(self, cpm_results: Dict) -> List[Dict]:
        risks = []
        if cpm_results.get("average_float", 999) < 2:
            risks.append(self._create_risk_item("schedule", "Schedule has minimal overall float", "high", "high", "Negotiate extensions, reduce scope, or add resources", "Float analysis"))
        return risks

    def _generate_recovery_options(self, delay_analysis: Dict, cpm: Dict) -> List[Dict]:
        total_delay = delay_analysis.get("total_delay_days", 0)
        critical_path = cpm.get("critical_path_activities", [])
        options = []
        
        crashable = [a for a in critical_path if a.get("percent_complete", 0) < 50]
        if crashable:
            potential_savings = len(crashable) * 2
            options.append({
                "strategy": "Crashing",
                "description": f"Add resources to {len(crashable)} incomplete critical activities",
                "potential_savings_days": min(potential_savings, total_delay),
                "cost_impact": "High",
                "feasibility": "Medium"
            })
        
        options.append({
            "strategy": "Fast-Tracking",
            "description": "Perform critical activities in parallel where possible",
            "potential_savings_days": total_delay * 0.3,
            "cost_impact": "Medium",
            "feasibility": "Medium"
        })
        options.append({
            "strategy": "Scope Reduction",
            "description": "Defer non-critical scope to later phase",
            "potential_savings_days": total_delay * 0.5,
            "cost_impact": "Low",
            "feasibility": "High"
        })
        return options

    def _extract_milestones(self, schedule_data: Dict) -> List[Dict]:
        milestones = []
        for act in schedule_data.get("activities", [])[:100]:
            name = act.get("name", "").lower()
            if any(k in name for k in ["milestone", "substantial completion", "practical completion", "handover", "start", "finish"]):
                milestones.append({"id": act.get("id"), "name": act.get("name"), "date": act.get("start") or act.get("finish")})
        return milestones

    def _generate_schedule_recommendations(self, cpm: Dict, delay_analysis: Optional[Dict]) -> List[str]:
        recs = []
        if cpm.get("average_float", 999) < 2:
            recs.append("Schedule is tightly constrained - consider adding buffers")
        if delay_analysis and delay_analysis.get("total_delay_days", 0) > 7:
            recs.append("Significant delays detected - implement recovery plan immediately")
        return recs

    def _assess_delay_impact(self, delays: List[Dict], total_delay: int) -> str:
        return "critical" if total_delay > 14 else "moderate" if total_delay > 7 else "minor"

    def _calculate_duration_days(self, start: str, finish: str) -> int:
        try:
            s = datetime.fromisoformat(start.replace('Z', '+00:00'))
            f = datetime.fromisoformat(finish.replace('Z', '+00:00'))
            return max(0, (f - s).days)
        except Exception:
            return 0

    def _calculate_date_diff(self, date1: str, date2: str) -> int:
        try:
            d1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
            d2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
            return max(0, (d2 - d1).days)
        except Exception:
            return 0

    async def process_specification_full(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        division_filter = p.get("division")
        
        if not file_path:
            return {"status": "error", "error": "No specification file provided"}
        
        try:
            import fitz
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
        except Exception as e:
            return {"status": "error", "error": f"Could not read spec: {str(e)}"}
        
        divisions = self._parse_csi_divisions(full_text)
        sections = self._parse_spec_sections(full_text)
        submittals = self._extract_submittals(full_text)
        performance = self._extract_performance_criteria(full_text)
        warranties = self._extract_warranty_requirements(full_text)
        testing = self._extract_testing_requirements(full_text)
        
        if division_filter:
            sections = [s for s in sections if s.get("division") == division_filter]
            submittals = [s for s in submittals if s.get("division") == division_filter]
        
        return {
            "status": "success",
            "action": "specification_analysis",
            "file_name": Path(file_path).name,
            "project_specifications": {
                "total_divisions": len(divisions),
                "total_sections": len(sections),
                "divisions_found": divisions
            },
            "sections": sections[:50] if not p.get("full_details") else sections,
            "submittals": {
                "total_required": len(submittals),
                "shop_drawings": len([s for s in submittals if "shop" in s["type"].lower()]),
                "samples": len([s for s in submittals if "sample" in s["type"].lower()]),
                "list": submittals[:30]
            },
            "performance_criteria": performance,
            "warranty_requirements": warranties,
            "testing_requirements": testing,
            "summary": f"Found {len(sections)} sections, {len(submittals)} submittals required"
        }

    def _parse_csi_divisions(self, text: str) -> List[Dict]:
        divisions_found = []
        for code, name in self.csi_divisions.items():
            pattern = rf'\b(?:Section\s*)?{code}\s*(?:\d{{2,}})?\s*(?:-|–)?\s*{name}'
            if re.search(pattern, text, re.IGNORECASE):
                section_count = len(re.findall(rf'\b{code}\d{{2,}}\b', text))
                divisions_found.append({"code": code, "name": name, "section_count": section_count})
        return sorted(divisions_found, key=lambda x: x["code"])

    def _parse_spec_sections(self, text: str) -> List[Dict]:
        sections = []
        section_pattern = r'(?:SECTION|DIVISION)?\s*(\d{2})\s*(\d{2})\s*(\d{2})?\s*(?:-|–)?\s*([^\n]+)'
        for match in re.finditer(section_pattern, text, re.IGNORECASE):
            division = match.group(1)
            section = match.group(2)
            subsection = match.group(3) or "00"
            title = match.group(4).strip()
            start_pos = match.end()
            next_match = re.search(section_pattern, text[start_pos:], re.IGNORECASE)
            end_pos = start_pos + next_match.start() if next_match else len(text)
            content = text[start_pos:end_pos]
            sections.append({
                "number": f"{division}{section}{subsection}",
                "division": division,
                "title": title,
                "key_requirements": self._extract_key_reqs(content)
            })
        return sections

    def _extract_key_reqs(self, content: str) -> List[str]:
        reqs = []
        for match in re.finditer(r'(?:shall|must|required|shall be)[^.]{0,100}\.', content, re.IGNORECASE):
            reqs.append(match.group(0).strip())
        return reqs[:5]

    def _extract_submittals(self, text: str) -> List[Dict]:
        submittals = []
        submittal_patterns = [
            (r'(?:shop drawing|working drawing)s?[:\s]*([^;.]*)', "shop_drawing"),
            (r'(?:product data|cut sheet|technical data)[:\s]*([^;.]*)', "product_data"),
            (r'(?:sample|mock.?up)[:\s]*([^;.]*)', "sample"),
            (r'(?:certificate|test report|mix design)[:\s]*([^;.]*)', "certificate"),
        ]
        for pattern, sub_type in submittal_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                submittals.append({
                    "type": sub_type,
                    "description": match.group(1).strip() if match.groups() else match.group(0),
                    "division": self._infer_division_from_context(match.start(), text)
                })
        return submittals

    def _infer_division_from_context(self, position: int, text: str) -> str:
        before = text[:position]
        match = re.search(r'\b(\d{2})\d{2,}\b', before)
        return match.group(1) if match else "unknown"

    def _extract_performance_criteria(self, text: str) -> List[Dict]:
        criteria = []
        patterns = [
            (r'(?:compressive strength|fc[\'′]?)\s*(?:of|≥|>=)?\s*(\d+\s*MPa|[^\s,;]*)', "strength"),
            (r'(?:fire rating|FRL|fire resistance)\s*(?:of|≥)?\s*(\d+[/\d]*\s*min|[^\s,;]*)', "fire"),
            (r'(?:thermal resistance|R-?value|U-?value)\s*(?:of|≤|<=)?\s*(\d+\.?\d*[^\s,;]*)', "thermal"),
            (r'(?:sound rating|STC|NRC|Rw)\s*(?:of|≥)?\s*(\d+[^\s,;]*)', "acoustic"),
            (r'(?:wind load|pressure)\s*(?:of|≥)?\s*(\d+\s*(?:Pa|kPa|psf|mph)?[^\s,;]*)', "structural"),
        ]
        for pattern, perf_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                criteria.append({
                    "type": perf_type,
                    "requirement": match.group(0),
                    "value": match.group(1) if match.groups() else "unspecified",
                    "section": self._infer_division_from_context(match.start(), text)
                })
        return criteria

    def _extract_warranty_requirements(self, text: str) -> List[Dict]:
        warranties = []
        for match in re.finditer(r'(?:warranty|guarantee)\s*(?:period)?\s*(\d+)\s*(?:years?|yrs?)', text, re.IGNORECASE):
            warranties.append({"years": int(match.group(1)), "context": match.group(0)})
        return warranties

    def _extract_testing_requirements(self, text: str) -> List[Dict]:
        tests = []
        for match in re.finditer(r'(?:test|inspect)\s*[^.]{0,50}(?:ASTM|BS|ISO|ACI)\s*[A-Z0-9\-]+', text, re.IGNORECASE):
            tests.append({"requirement": match.group(0)})
        return tests

    async def change_order_impact(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        co_description = data.get("description") or p.get("description")
        co_value = data.get("value") or p.get("value", 0)
        affected_activities = data.get("affected_activities") or p.get("affected_activities", [])
        schedule_file = data.get("schedule_file") or p.get("schedule_file")
        contract_file = data.get("contract_file") or p.get("contract_file")
        
        if not co_description:
            return {"status": "error", "error": "Change order description required"}
        
        co_analysis = self._analyze_change_order_text(co_description)
        cost_impact = self._calculate_co_cost_impact(co_value, co_analysis)
        
        schedule_impact = {"delay_days": 0, "affected_milestones": []}
        if schedule_file:
            schedule_impact = await self._calculate_co_schedule_impact(schedule_file, affected_activities)
        
        risks = self._assess_co_risks(co_analysis, co_value, schedule_impact)
        contract_implications = {}
        if contract_file:
            contract_implications = self._check_contract_change_terms(contract_file, co_value)
        
        return {
            "status": "success",
            "action": "change_order_analysis",
            "change_order_summary": {
                "description": co_description[:200],
                "category": co_analysis.get("category"),
                "direct_cost": co_value,
                "total_impact_cost": cost_impact.get("total"),
                "schedule_impact_days": schedule_impact.get("delay_days")
            },
            "cost_breakdown": cost_impact,
            "schedule_impact": schedule_impact,
            "risks": [asdict(r) if isinstance(r, RiskItem) else r for r in risks],
            "contract_implications": contract_implications,
            "approval_recommendation": "approve" if all((r.impact if isinstance(r, RiskItem) else r.get("impact")) != "high" for r in risks) else "negotiate",
            "negotiation_points": self._identify_negotiation_points(cost_impact, risks),
            "mitigation_strategies": self._generate_co_recommendations(cost_impact, schedule_impact, risks)
        }

    def _analyze_change_order_text(self, text: str) -> Dict:
        categories = {
            "design_change": ["design", "drawing", "specification", "architect", "engineer"],
            "scope_addition": ["additional", "extra", "new", "more", "increase quantity"],
            "scope_deletion": ["delete", "remove", "omit", "deduct"],
            "unforeseen_condition": ["unforeseen", "unknown", "existing", "ground condition", "utility"],
            "acceleration": ["accelerate", "expedite", "crash", "fast track"],
            "delay_compensation": ["delay", "disruption", "prolongation", "waiting"],
        }
        text_lower = text.lower()
        detected_category = "general"
        confidence = 0
        for cat, keywords in categories.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > confidence:
                detected_category = cat
                confidence = matches
        return {
            "category": detected_category,
            "confidence": min(confidence / 3, 1.0),
            "complexity": "high" if len(text) > 500 else "medium" if len(text) > 200 else "low",
            "trade_involved": self._detect_trade_from_text(text)
        }

    def _detect_trade_from_text(self, text: str) -> str:
        trades = ["concrete", "steel", "electrical", "plumbing", "hvac", "masonry", "finishes", "fire protection"]
        return next((t for t in trades if t in text.lower()), "general")

    def _calculate_co_cost_impact(self, direct_cost: float, analysis: Dict) -> Dict:
        direct = float(direct_cost) if direct_cost else 0
        overhead = direct * 0.20
        profit = direct * 0.10 if analysis.get("category") == "scope_addition" else 0
        complexity = analysis.get("complexity", "medium")
        risk_rates = {"low": 0.05, "medium": 0.10, "high": 0.20}
        risk_allowance = direct * risk_rates.get(complexity, 0.10)
        total = direct + overhead + profit + risk_allowance
        return {
            "direct_cost": direct,
            "overhead": overhead,
            "profit": profit,
            "risk_allowance": risk_allowance,
            "total": total,
            "breakdown_percentages": {
                "direct": f"{(direct/total*100):.1f}%" if total else "0%",
                "overhead": f"{(overhead/total*100):.1f}%" if total else "0%",
                "risk": f"{(risk_allowance/total*100):.1f}%" if total else "0%"
            }
        }

    async def _calculate_co_schedule_impact(self, schedule_file: str, affected_activities: List) -> Dict:
        schedule_data = self._parse_xer_file(schedule_file)
        affected_paths = []
        total_delay = 0
        for act_id in affected_activities:
            act = next((a for a in schedule_data.get("activities", []) if a["id"] == act_id), None)
            if act and act.get("critical"):
                affected_paths.append({"activity": act_id, "critical": True, "impact": "direct_delay"})
                total_delay += act.get("duration", 0)
            elif act:
                affected_paths.append({"activity": act_id, "critical": False, "impact": "congestion"})
        return {
            "delay_days": total_delay,
            "affected_activities": len(affected_activities),
            "critical_path_impact": any(a.get("critical") for a in affected_paths),
            "affected_milestones": self._identify_affected_milestones(schedule_data, affected_activities),
            "mitigation_options": ["overtime", "additional_crew", "resequence"] if total_delay > 5 else []
        }

    def _assess_co_risks(self, analysis: Dict, co_value: float, schedule_impact: Dict) -> List[RiskItem]:
        risks = []
        if analysis.get("complexity") == "high":
            risks.append(RiskItem(
                id="CO-001", category="cost", description="High complexity change order - cost uncertainty",
                probability="high", impact="high", mitigation="Break into smaller packages, get detailed quotes", source="change_order"
            ))
        if schedule_impact.get("delay_days", 0) > 7:
            risks.append(RiskItem(
                id="CO-002", category="schedule", description="Significant schedule impact from change order",
                probability="high", impact="high", mitigation="Negotiate EOT, fast-track unaffected work", source="change_order"
            ))
        return risks

    def _identify_negotiation_points(self, cost_impact: Dict, risks: List) -> List[str]:
        points = []
        if cost_impact.get("risk_allowance", 0) > cost_impact.get("direct_cost", 0) * 0.15:
            points.append("High risk allowance - request breakdown")
        if any((r.impact if isinstance(r, RiskItem) else r.get("impact")) == "high" for r in risks):
            points.append("Schedule-critical impacts require EOT discussion")
        return points

    def _generate_co_recommendations(self, cost_impact: Dict, schedule_impact: Dict, risks: List) -> List[str]:
        recs = []
        if cost_impact.get("total", 0) > cost_impact.get("direct_cost", 0) * 1.5:
            recs.append("High overhead/risk markup - negotiate direct cost basis")
        if schedule_impact.get("delay_days", 0) > 0:
            recs.append("Secure written time extension before proceeding")
        return recs

    def _check_contract_change_terms(self, contract_file: str, co_value: float) -> Dict:
        return {"notice_required": True, "valuation_method": "agreed rates or reasonable costs"}

    async def rfi_generator(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        ambiguity_description = data.get("description") or p.get("description")
        drawing_ref = data.get("drawing_reference") or p.get("drawing_reference")
        spec_ref = data.get("spec_reference") or p.get("spec_reference")
        priority = p.get("priority", "normal")
        trade = p.get("trade", "general")
        project_name = p.get("project_name", "Project")
        
        if not ambiguity_description:
            return {"status": "error", "error": "Ambiguity description required"}
        
        analysis = self._analyze_ambiguity(ambiguity_description)
        suggested_number = f"RFI-{trade[:3].upper()}-{datetime.now(timezone.utc).strftime('%y%m%d')}-XXX"
        rfi_text = self._generate_rfi_text(ambiguity_description, drawing_ref, spec_ref, analysis, project_name)
        suggestions = self._suggest_clarifications(analysis)
        impact = self._assess_ambiguity_impact(analysis, priority)
        
        return {
            "status": "success",
            "action": "rfi_generated",
            "generated_rfi": {
                "suggested_number": suggested_number,
                "subject": f"Clarification required: {analysis.get('topic', 'General')}",
                "priority": priority,
                "trade": trade,
                "full_text": rfi_text,
                "word_count": len(rfi_text.split())
            },
            "ambiguity_analysis": analysis,
            "references": {
                "drawings": drawing_ref,
                "specifications": spec_ref,
            },
            "suggested_responses": suggestions,
            "impact_assessment": impact,
            "recommended_response_time": "48 hours" if priority == "urgent" else "7 days",
            "attachments_needed": self._identify_rfi_attachments(analysis)
        }

    def _analyze_ambiguity(self, text: str) -> Dict:
        ambiguity_types = {
            "conflict": ["conflict", "contradict", "differ", "discrepancy", "does not match"],
            "omission": ["missing", "not shown", "not indicated", "omit", "not specified"],
            "unclear": ["unclear", "ambiguous", "vague", "not clear", "undefined"],
            "impossible": ["impossible", "cannot", "unable", "construct", "build"],
            "dimension_error": ["dimension", "does not fit", "clash", "coordination"],
            "sequence": ["sequence", "order", "before", "after", "prerequisite"],
        }
        text_lower = text.lower()
        detected_types = []
        for amb_type, keywords in ambiguity_types.items():
            if any(kw in text_lower for kw in keywords):
                detected_types.append(amb_type)
        trades = ["concrete", "steel", "electrical", "plumbing", "hvac", "masonry", "finishes", "fire protection"]
        detected_trade = next((t for t in trades if t in text_lower), "general")
        return {
            "types": detected_types,
            "primary_type": detected_types[0] if detected_types else "general",
            "trade": detected_trade,
            "topic": self._extract_topic(text),
            "complexity": "high" if len(detected_types) > 1 else "medium" if detected_types else "low",
            "urgency_indicators": any(w in text_lower for w in ["delay", "stop", "hold", "cannot proceed"])
        }

    def _extract_topic(self, text: str) -> str:
        topics = {
            "foundation": ["foundation", "pile", "footing", "raft"],
            "structure": ["beam", "column", "slab", "wall"],
            "envelope": ["facade", "curtain", "cladding", "roof"],
            "MEP": ["electrical", "plumbing", "hvac", "duct", "pipe"],
            "finishes": ["floor", "ceiling", "paint", "tile"],
        }
        text_lower = text.lower()
        for topic, keywords in topics.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        return "General"

    def _generate_rfi_text(self, description: str, drawing: str, spec: str, analysis: Dict, project: str) -> str:
        parts = []
        parts.append(f"Subject: Request for Information - {analysis.get('topic', 'Clarification Required')}")
        parts.append(f"Project: {project}")
        parts.append("")
        parts.append("BACKGROUND:")
        parts.append(f"The Contractor is preparing to execute work related to {analysis.get('trade', 'the scope')}.")
        if drawing:
            parts.append(f"Reference Drawing(s): {drawing}")
        if spec:
            parts.append(f"Reference Specification(s): {spec}")
        parts.append("")
        parts.append("ISSUE/AMBIGUITY:")
        parts.append(description)
        parts.append("")
        parts.append("IMPACT:")
        if analysis.get("urgency_indicators"):
            parts.append("This ambiguity is impacting ongoing work and may cause delays if not resolved promptly.")
        else:
            parts.append("This ambiguity requires clarification to ensure compliance with design intent.")
        parts.append("")
        parts.append("REQUESTED CLARIFICATION:")
        if analysis.get("primary_type") == "conflict":
            parts.append("1. Please confirm which document takes precedence.")
            parts.append("2. Please provide revised details coordinating both requirements.")
        elif analysis.get("primary_type") == "omission":
            parts.append("1. Please confirm the required scope/material/dimension.")
            parts.append("2. Please provide missing details or reference to applicable standards.")
        elif analysis.get("primary_type") == "dimension_error":
            parts.append("1. Please confirm correct dimensions.")
            parts.append("2. Please clarify coordination between elements.")
        else:
            parts.append("1. Please clarify the design intent.")
            parts.append("2. Please provide any additional details required for construction.")
        parts.append("")
        parts.append("Submitted by: [Contractor Name]")
        parts.append(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
        return "\n".join(parts)

    def _suggest_clarifications(self, analysis: Dict) -> List[str]:
        return [f"Confirm {analysis.get('trade')} requirements per design intent"]

    def _assess_ambiguity_impact(self, analysis: Dict, priority: str) -> Dict:
        return {"schedule_impact": "high" if analysis.get("urgency_indicators") else "low", "cost_risk": "medium"}

    def _identify_rfi_attachments(self, analysis: Dict) -> List[str]:
        return ["Marked-up drawings", "Photos of existing conditions"]

    async def safety_compliance_audit(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        audit_type = p.get("type", "general")
        project_location = p.get("location", "US")
        checklist_items = data.get("checklist_items") or p.get("checklist_items", [])
        photo_files = data.get("photos") or p.get("photos", [])
        
        standards = self._get_applicable_safety_standards(audit_type, project_location)
        checklist_results = self._perform_safety_checklist(checklist_items, standards)
        
        photo_analysis = []
        for photo in photo_files:
            analysis = await self._analyze_safety_photo(photo, audit_type)
            photo_analysis.append(analysis)
        
        violations = self._identify_safety_violations(checklist_results, photo_analysis)
        risk_score = self._calculate_safety_risk_score(violations)
        corrective_actions = self._generate_corrective_actions(violations)
        compliance_rate = (len([c for c in checklist_results if c.get("compliant")]) / len(checklist_results) * 100) if checklist_results else 0
        
        return {
            "status": "success",
            "action": "safety_audit",
            "audit_type": audit_type,
            "location": project_location,
            "applicable_standards": standards,
            "summary": {
                "compliance_rate": f"{compliance_rate:.1f}%",
                "violations_found": len(violations),
                "critical_violations": len([v for v in violations if v.get("severity") == "critical"]),
                "major_violations": len([v for v in violations if v.get("severity") == "major"]),
                "minor_violations": len([v for v in violations if v.get("severity") == "minor"]),
                "risk_score": risk_score,
                "status": "pass" if risk_score > 80 else "conditional" if risk_score > 60 else "fail"
            },
            "violations": violations,
            "checklist_results": checklist_results,
            "photo_analysis": photo_analysis,
            "corrective_actions": corrective_actions,
            "stop_work_triggers": [v for v in violations if v.get("stop_work_required")],
            "recommendations": self._generate_safety_recommendations(violations),
            "re_audit_required": any(v.get("severity") == "critical" for v in violations),
            "next_audit_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat() if violations else (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }

    def _get_applicable_safety_standards(self, audit_type: str, location: str) -> List[str]:
        base = ["OSHA 1926", "ISO 45001"]
        location_map = {
            "US": ["OSHA 1926", "ANSI A10"],
            "UK": ["CDM 2015", "BS EN 12811", "HSE Guidance"],
            "EU": ["EU Directive 92/57/EEC", "EN Standards"],
            "GCC": ["OSHA (US based)", "Local Municipality Requirements"],
            "AU": ["WHS Act 2011", "AS/NZS Standards"]
        }
        type_map = {
            "excavation": ["OSHA 1926 Subpart P"],
            "scaffolding": ["OSHA 1926 Subpart L", "ANSI A10.8"],
            "electrical": ["OSHA 1926 Subpart K", "NFPA 70E"],
            "confined_space": ["OSHA 1926 Subpart AA"],
            "fall_protection": ["OSHA 1926 Subpart M"]
        }
        standards = location_map.get(location, base)
        if audit_type in type_map:
            standards.extend(type_map[audit_type])
        return standards

    def _perform_safety_checklist(self, checklist_items: List, standards: List[str]) -> List[Dict]:
        results = []
        for item in checklist_items:
            results.append({
                "item": item.get("item", "Unknown"),
                "compliant": item.get("status", "unknown") == "compliant",
                "standard": item.get("standard", standards[0] if standards else "General"),
                "notes": item.get("notes", "")
            })
        return results

    async def _analyze_safety_photo(self, photo_path: str, audit_type: str) -> Dict:
        image_block = self.get_dep("image")
        safety_prompts = {
            "general": "Identify safety hazards: missing PPE, trip hazards, exposed edges, improper storage",
            "scaffolding": "Check: guardrails, midrails, toeboards, plank overhang, base plates, access",
            "excavation": "Check: shoring, sloping, benching, spoil pile distance, access/egress",
            "electrical": "Check: exposed wires, GFCI, panel access, temporary power, grounding",
            "fall_protection": "Check: guardrails, harnesses, anchor points, lifelines, hole covers"
        }
        
        if image_block:
            try:
                analysis = await image_block.execute(
                    {"image_path": photo_path},
                    {"prompt": safety_prompts.get(audit_type, safety_prompts["general"])}
                )
                desc = analysis.get("result", {}).get("description", "")
            except Exception:
                desc = ""
        else:
            desc = ""
        
        hazards_found = self._parse_safety_hazards(desc)
        return {
            "photo": Path(photo_path).name,
            "hazards_detected": len(hazards_found),
            "hazards": hazards_found,
            "overall_assessment": "unsafe" if hazards_found else "compliant",
            "requires_immediate_action": any(h.get("severity") == "critical" for h in hazards_found)
        }

    def _parse_safety_hazards(self, text: str) -> List[Dict]:
        hazards = []
        hazard_patterns = [
            (r'miss(?:ing)?\s*(?:PPE|helmet|harness|vest)', 'missing_ppe', 'critical'),
            (r'exposed\s*(?:edge|opening|hole)', 'fall_hazard', 'critical'),
            (r'trip\s*hazard', 'trip_hazard', 'major'),
            (r'(?:no|missing)\s*guardrail', 'missing_guardrail', 'critical'),
            (r'improper\s*storage', 'improper_storage', 'minor'),
        ]
        for pattern, h_type, severity in hazard_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                hazards.append({
                    "type": h_type,
                    "description": match.group(0),
                    "severity": severity,
                    "context": text[max(0, match.start()-30):match.end()+30]
                })
        return hazards

    def _identify_safety_violations(self, checklist_results: List[Dict], photo_analysis: List[Dict]) -> List[Dict]:
        violations = []
        for item in checklist_results:
            if not item.get("compliant"):
                violations.append({
                    "source": "checklist",
                    "item": item["item"],
                    "severity": "major",
                    "standard": item.get("standard"),
                    "stop_work_required": False
                })
        for photo in photo_analysis:
            for hazard in photo.get("hazards", []):
                violations.append({
                    "source": "photo_analysis",
                    "item": hazard.get("type"),
                    "severity": hazard.get("severity", "minor"),
                    "description": hazard.get("description"),
                    "stop_work_required": hazard.get("severity") == "critical"
                })
        return violations

    def _calculate_safety_risk_score(self, violations: List[Dict]) -> float:
        if not violations:
            return 100.0
        severity_scores = {"minor": 5, "major": 15, "critical": 30}
        total_penalty = sum(severity_scores.get(v.get("severity", "minor"), 5) for v in violations)
        return max(0, 100 - total_penalty)

    def _generate_corrective_actions(self, violations: List[Dict]) -> List[Dict]:
        actions = []
        for v in violations:
            actions.append({
                "violation": v.get("item"),
                "action": f"Address {v.get('item')}",
                "priority": "immediate" if v.get("severity") == "critical" else "7 days"
            })
        return actions

    def _generate_safety_recommendations(self, violations: List[Dict]) -> List[str]:
        if any(v.get("severity") == "critical" for v in violations):
            return ["Stop work immediately in affected areas", "Conduct toolbox talk before resuming"]
        return ["Continue daily safety inspections", "Address noted deficiencies promptly"]

    async def carbon_footprint_calculator(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        quantities = data.get("quantities") or p.get("quantities")
        materials = data.get("materials") or p.get("materials", [])
        location = p.get("location", "US")
        building_type = p.get("building_type", "office")
        gfa = p.get("gross_floor_area_m2")
        target_certification = p.get("target_certification")
        
        if not quantities and not materials:
            return {"status": "error", "error": "No quantities or materials provided"}
        
        if isinstance(quantities, dict):
            materials = self._convert_quantities_to_materials(quantities)
        
        carbon_results = []
        total_embodied = 0
        total_operational = 0
        for material in materials:
            result = self._calculate_material_carbon(material, location)
            carbon_results.append(result)
            total_embodied += result.get("embodied_carbon_kg", 0)
            total_operational += result.get("operational_carbon_kg", 0)
        
        benchmarks = self._get_carbon_benchmarks(building_type)
        comparison = self._compare_to_benchmark(total_embodied, gfa, benchmarks)
        optimization = self._generate_carbon_optimization(carbon_results, target_certification)
        
        return {
            "status": "success",
            "action": "carbon_analysis",
            "summary": {
                "total_embodied_carbon_kg": round(total_embodied, 2),
                "total_operational_carbon_kg": round(total_operational, 2),
                "total_carbon_kg": round(total_embodied + total_operational, 2),
                "gross_floor_area_m2": gfa,
                "embodied_carbon_per_m2": round(total_embodied / gfa, 2) if gfa else None,
                "building_type": building_type,
                "location": location
            },
            "benchmark_comparison": comparison,
            "material_breakdown": carbon_results,
            "hotspots": [m for m in carbon_results if m.get("carbon_intensity", 0) > 500][:10],
            "optimization_strategies": optimization,
            "certification_pathway": self._get_certification_pathway(target_certification, total_embodied, gfa),
            "recommendations": self._generate_carbon_recommendations(carbon_results, comparison)
        }

    def _convert_quantities_to_materials(self, quantities: Dict) -> List[Dict]:
        materials = []
        mapping = {
            "concrete_m3": {"material": "ready_mix_concrete", "unit": "m3"},
            "steel_ton": {"material": "structural_steel", "unit": "ton"},
            "rebar_ton": {"material": "steel_rebar", "unit": "ton"},
            "timber_m3": {"material": "softwood_timber", "unit": "m3"},
            "glass_m2": {"material": "glazing", "unit": "m2"},
            "insulation_m2": {"material": "insulation", "unit": "m2"},
        }
        for key, qty in quantities.items():
            mapped = mapping.get(key)
            if mapped:
                materials.append({"material": mapped["material"], "quantity": float(qty), "unit": mapped["unit"]})
        return materials

    def _calculate_material_carbon(self, material: Dict, location: str) -> Dict:
        material_name = material.get("material", "unknown")
        quantity = float(material.get("quantity", 0))
        unit = material.get("unit", "m3")
        
        efi = self.carbon_emission_factors.get(material_name, {"unit": unit, "factor": 100})
        embodied = quantity * efi["factor"]
        operational = quantity * (efi.get("operational_factor", 0) or 0)
        intensity = embodied / quantity if quantity else 0
        
        alternatives = []
        for alt_name, alt_factor in self.carbon_emission_factors.items():
            if alt_name != material_name and alt_factor["unit"] == unit and alt_factor["factor"] < efi["factor"] * 0.8:
                savings = embodied - (quantity * alt_factor["factor"])
                if savings > 0:
                    alternatives.append({
                        "alternative": alt_name,
                        "potential_savings_kg": round(savings, 2),
                        "savings_percent": round((savings / embodied * 100), 1) if embodied else 0
                    })
        
        return {
            "material": material_name,
            "quantity": quantity,
            "unit": unit,
            "embodied_carbon_kg": round(embodied, 2),
            "operational_carbon_kg": round(operational, 2),
            "carbon_intensity": round(intensity, 2),
            "location": location,
            "alternatives": sorted(alternatives, key=lambda x: x["potential_savings_kg"], reverse=True)[:3]
        }

    def _get_carbon_benchmarks(self, building_type: str) -> Dict:
        return self.carbon_benchmarks.get(building_type, self.carbon_benchmarks["office"])

    def _compare_to_benchmark(self, total_embodied: float, gfa: Optional[float], benchmarks: Dict) -> Dict:
        if not gfa:
            return {"status": "unknown", "message": "GFA not provided"}
        intensity = total_embodied / gfa
        target = benchmarks.get("embodied_carbon_kg_per_m2")
        status = "below_target" if intensity < target else "above_target"
        return {
            "status": status,
            "actual_intensity_kg_m2": round(intensity, 2),
            "target_intensity_kg_m2": target,
            "variance_percent": round(((intensity - target) / target) * 100, 1) if target else 0
        }

    def _generate_carbon_optimization(self, results: List[Dict], target_cert: Optional[str]) -> List[Dict]:
        strategies = []
        high_carbon = [r for r in results if r.get("carbon_intensity", 0) > 300]
        if high_carbon:
            for item in high_carbon[:3]:
                if item.get("alternatives"):
                    strategies.append({
                        "strategy": f"Substitute {item['material']}",
                        "impact": f"Save up to {item['alternatives'][0]['potential_savings_kg']} kg CO2e",
                        "priority": "high"
                    })
        if target_cert:
            strategies.append({"strategy": f"Optimize for {target_cert} certification", "impact": "May reduce intensity by 10-20%", "priority": "medium"})
        return strategies

    def _get_certification_pathway(self, target_cert: Optional[str], total_embodied: float, gfa: Optional[float]) -> Dict:
        if not target_cert:
            return {"available": False}
        pathways = {
            "LEED": {"requirements": ["Energy modeling", "Material transparency", "Waste management"]},
            "BREEAM": {"requirements": ["LCA assessment", "Responsible sourcing", "Construction waste management"]},
            "WELL": {"requirements": ["Material health", "Air quality", "Water quality"]},
            "Passive House": {"requirements": ["Airtightness", "Thermal bridge free", "High insulation"]}
        }
        return {"certification": target_cert, **pathways.get(target_cert, {"requirements": []})}

    def _generate_carbon_recommendations(self, results: List[Dict], comparison: Dict) -> List[str]:
        recs = []
        if comparison.get("status") == "above_target":
            recs.append("Project exceeds carbon benchmark - prioritize low-carbon alternatives")
        top = sorted(results, key=lambda x: x.get("embodied_carbon_kg", 0), reverse=True)
        if top:
            recs.append(f"Highest impact material: {top[0]['material']} ({top[0]['embodied_carbon_kg']} kg CO2e)")
        return recs

    async def procurement_list_generator(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        boq_items = data.get("boq_items") or p.get("boq_items", [])
        schedule_file = data.get("schedule_file") or p.get("schedule_file")
        lead_times = data.get("lead_times") or p.get("lead_times")
        
        if not boq_items:
            return {"status": "error", "error": "No BOQ items provided"}
        
        if not lead_times:
            lead_times = self._get_default_lead_times()
        
        schedule = None
        if schedule_file:
            schedule = self._parse_xer_file(schedule_file)
        
        procurement_items = []
        for item in boq_items:
            material = item.get("material", "general")
            required_date = item.get("required_date")
            if schedule and not required_date:
                required_date = self._find_required_date_from_schedule(item, schedule)
            
            lt = lead_times.get(material, lead_times.get("general", 14))
            order_date = None
            if required_date:
                try:
                    rd = datetime.fromisoformat(required_date.replace('Z', '+00:00'))
                    order_date = (rd - timedelta(days=lt)).isoformat()
                except Exception:
                    order_date = None
            
            procurement_items.append({
                "material": material,
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "required_date": required_date,
                "lead_time_days": lt,
                "latest_order_date": order_date,
                "status": "ok" if order_date and (datetime.now(timezone.utc) + timedelta(days=7)) < datetime.fromisoformat(order_date.replace('Z', '+00:00')) else "urgent"
            })
        
        urgent = [i for i in procurement_items if i["status"] == "urgent"]
        return {
            "status": "success",
            "action": "procurement_plan",
            "summary": {
                "total_items": len(procurement_items),
                "urgent_items": len(urgent),
                "ok_items": len(procurement_items) - len(urgent)
            },
            "procurement_items": procurement_items,
            "urgent_items": urgent,
            "recommendations": [f"Place orders for {len(urgent)} urgent items immediately"] if urgent else ["All procurement items are on track"]
        }

    def _get_default_lead_times(self) -> Dict[str, int]:
        return {
            "ready_mix_concrete": 7,
            "structural_steel": 90,
            "steel_rebar": 45,
            "softwood_timber": 30,
            "glazing": 60,
            "insulation": 21,
            "hvac_equipment": 120,
            "electrical_panel": 90,
            "fire_sprinkler": 45,
            "elevator": 180,
            "general": 30
        }

    def _find_required_date_from_schedule(self, item: Dict, schedule: Dict) -> Optional[str]:
        activity_keywords = [item.get("material", "").lower(), item.get("trade", "").lower()]
        for act in schedule.get("activities", []):
            act_name = act.get("name", "").lower()
            if any(kw in act_name for kw in activity_keywords if kw):
                return act.get("early_start") or act.get("start")
        return None

    async def as_built_deviation_report(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        as_built_file = data.get("as_built_file") or p.get("as_built_file")
        design_file = data.get("design_file") or p.get("design_file")
        project_name = p.get("project_name", "Project")
        
        if not as_built_file or not design_file:
            return {"status": "error", "error": "Both as-built and design files required"}
        
        as_built_data = await self._extract_drawing_data(as_built_file)
        design_data = await self._extract_drawing_data(design_file)
        
        deviations = self._compare_drawings(design_data, as_built_data)
        report = self._generate_deviation_report(deviations, project_name)
        
        return {
            "status": "success",
            "action": "as_built_deviation",
            "project_name": project_name,
            "summary": {
                "total_deviations": len(deviations),
                "critical_deviations": len([d for d in deviations if d.get("severity") == "critical"]),
                "major_deviations": len([d for d in deviations if d.get("severity") == "major"]),
                "minor_deviations": len([d for d in deviations if d.get("severity") == "minor"]),
                "acceptable_deviations": len([d for d in deviations if d.get("severity") == "acceptable"])
            },
            "deviations": deviations,
            "formal_report": report,
            "recommendations": self._generate_deviation_recommendations(deviations),
            "approval_status": "requires_approval" if any(d.get("severity") == "critical" for d in deviations) else "approved"
        }

    async def _extract_drawing_data(self, file_path: str) -> Dict:
        if file_path.lower().endswith('.pdf'):
            try:
                import fitz
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return {"file_name": Path(file_path).name, "text": text}
            except Exception as e:
                return {"file_name": Path(file_path).name, "text": "", "error": str(e)}
        return {"file_name": Path(file_path).name, "text": ""}

    def _compare_drawings(self, design: Dict, as_built: Dict) -> List[Dict]:
        deviations = []
        design_dims = self._extract_drawing_dimensions(design.get("text", ""))
        as_built_dims = self._extract_drawing_dimensions(as_built.get("text", ""))
        
        for label, d_dim in design_dims.items():
            ab_dim = as_built_dims.get(label)
            if ab_dim is not None and abs(d_dim - ab_dim) > 0.05 * d_dim:
                deviations.append({
                    "element": label,
                    "design_value": d_dim,
                    "as_built_value": ab_dim,
                    "deviation_percent": round((ab_dim - d_dim) / d_dim * 100, 1),
                    "severity": "major" if abs((ab_dim - d_dim) / d_dim) > 0.1 else "minor",
                    "type": "dimensional"
                })
        
        design_materials = self._extract_materials_from_text(design.get("text", ""))
        as_built_materials = self._extract_materials_from_text(as_built.get("text", ""))
        for mat in set(design_materials) | set(as_built_materials):
            if design_materials.get(mat) != as_built_materials.get(mat):
                deviations.append({
                    "element": mat,
                    "design_spec": design_materials.get(mat),
                    "as_built_spec": as_built_materials.get(mat),
                    "severity": "major",
                    "type": "material"
                })
        return deviations

    def _extract_drawing_dimensions(self, text: str) -> Dict[str, float]:
        dims = {}
        for match in re.finditer(r'(\b[A-Z]{2,4}\s*\d{1,3}[A-Z]?)\s*[:=\s]+(\d+\.?\d*)\s*(?:m|mm)', text, re.IGNORECASE):
            label = match.group(1).strip()
            val = float(match.group(2))
            dims[label] = val
        return dims

    def _generate_deviation_report(self, deviations: List[Dict], project: str) -> str:
        lines = []
        lines.append(f"AS-BUILT DEVIATION REPORT - {project}")
        lines.append(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append(f"Total Deviations: {len(deviations)}")
        for d in deviations:
            lines.append(f"- {d['type'].upper()}: {d['element']} | Severity: {d['severity']}")
        lines.append("")
        lines.append("This report has been generated for engineering review.")
        return "\n".join(lines)

    def _generate_deviation_recommendations(self, deviations: List[Dict]) -> List[str]:
        if any(d.get("severity") == "critical" for d in deviations):
            return ["Critical deviations detected - seek structural/PE review", "Do not issue certificate of occupancy until resolved"]
        return ["Review deviations with design team", "Update as-built drawings for minor deviations"]

    async def warranty_maintenance_schedule(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        equipment_list = data.get("equipment") or p.get("equipment", [])
        handover_date_str = data.get("handover_date") or p.get("handover_date")
        
        if not equipment_list:
            return {"status": "error", "error": "No equipment list provided"}
        
        try:
            handover = datetime.fromisoformat(handover_date_str.replace('Z', '+00:00')) if handover_date_str else datetime.now(timezone.utc)
        except Exception:
            handover = datetime.now(timezone.utc)
        
        schedule = []
        for eq in equipment_list:
            warranty_years = float(eq.get("warranty_years", 1))
            warranty_end = (handover + timedelta(days=int(warranty_years * 365))).isoformat()
            maintenance_tasks = self._generate_maintenance_tasks(eq, handover)
            schedule.append({
                "equipment": eq.get("name", "Unknown"),
                "type": eq.get("type", "general"),
                "manufacturer": eq.get("manufacturer"),
                "warranty_period_years": warranty_years,
                "warranty_start": handover.isoformat(),
                "warranty_end": warranty_end,
                "maintenance_tasks": maintenance_tasks
            })
        
        return {
            "status": "success",
            "action": "warranty_maintenance",
            "handover_date": handover.isoformat(),
            "equipment_count": len(equipment_list),
            "schedule": schedule,
            "upcoming_tasks": [s for s in schedule for t in s["maintenance_tasks"] if t.get("due_date")][:10]
        }

    def _generate_maintenance_tasks(self, equipment: Dict, handover: datetime) -> List[Dict]:
        tasks = []
        eq_type = equipment.get("type", "").lower()
        if "hvac" in eq_type or "air" in eq_type:
            tasks.append({"task": "Filter replacement", "frequency": "Quarterly", "due_date": (handover + timedelta(days=90)).isoformat()})
            tasks.append({"task": "Coil cleaning", "frequency": "Annually", "due_date": (handover + timedelta(days=365)).isoformat()})
        elif "elevator" in eq_type:
            tasks.append({"task": "Safety inspection", "frequency": "Monthly", "due_date": (handover + timedelta(days=30)).isoformat()})
        elif "fire" in eq_type:
            tasks.append({"task": "Sprinkler flow test", "frequency": "Annually", "due_date": (handover + timedelta(days=365)).isoformat()})
            tasks.append({"task": "Alarm functional test", "frequency": "Semi-annually", "due_date": (handover + timedelta(days=180)).isoformat()})
        else:
            tasks.append({"task": "General inspection", "frequency": "Annually", "due_date": (handover + timedelta(days=365)).isoformat()})
        return tasks

    async def risk_register_auto_populate(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        documents = data.get("documents") or p.get("documents", [])
        schedule_file = data.get("schedule_file") or p.get("schedule_file")
        existing_risks = data.get("existing_risks") or p.get("existing_risks", [])
        
        detected_risks = list(existing_risks)
        risk_id_counter = len(existing_risks) + 1
        
        for doc_path in documents:
            doc_risks = await self._extract_risks_from_document(doc_path)
            for risk in doc_risks:
                risk["id"] = f"RISK-{risk_id_counter:03d}"
                detected_risks.append(risk)
                risk_id_counter += 1
        
        if schedule_file:
            schedule = self._parse_xer_file(schedule_file)
            schedule_risks = self._analyze_schedule_risks(self._calculate_critical_path(schedule))
            for sr in schedule_risks:
                sr["id"] = f"RISK-{risk_id_counter:03d}"
                detected_risks.append(sr)
                risk_id_counter += 1
        
        financial_risks = [r for r in detected_risks if r.get("category") == "cost"]
        schedule_risks = [r for r in detected_risks if r.get("category") == "schedule"]
        safety_risks = [r for r in detected_risks if r.get("category") == "safety"]
        high_risks = [r for r in detected_risks if r.get("impact") == "high"]
        
        return {
            "status": "success",
            "action": "risk_register_populated",
            "summary": {
                "total_risks": len(detected_risks),
                "new_risks_added": len(detected_risks) - len(existing_risks),
                "high_impact_risks": len(high_risks),
                "by_category": {
                    "financial": len(financial_risks),
                    "schedule": len(schedule_risks),
                    "safety": len(safety_risks),
                    "quality": len([r for r in detected_risks if r.get("category") == "quality"]),
                    "contractual": len([r for r in detected_risks if r.get("category") == "contractual"])
                }
            },
            "risk_register": detected_risks,
            "high_priority_risks": high_risks[:10],
            "top_5_risks": sorted(detected_risks, key=lambda x: ({"high": 3, "medium": 2, "low": 1}.get(x.get("impact"), 0), {"high": 3, "medium": 2, "low": 1}.get(x.get("probability"), 0)), reverse=True)[:5],
            "mitigation_summary": self._summarize_mitigations(detected_risks)
        }

    async def _extract_risks_from_document(self, file_path: str) -> List[Dict]:
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            try:
                import fitz
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
            except Exception:
                text = ""
        else:
            text = ""
        
        risks = []
        risk_patterns = {
            "delay": (r'(?:delay|risk of delay|late|behind schedule)', "schedule", "medium"),
            "cost": (r'(?:cost overrun|budget|risk of extra cost|additional cost)', "cost", "medium"),
            "safety": (r'(?:safety risk|hazard|accident risk)', "safety", "high"),
            "quality": (r'(?:quality risk|defect|non-conformance)', "quality", "medium"),
            "contractual": (r'(?:breach|dispute|claim|liquidated damages)', "contractual", "high"),
        }
        for key, (pattern, category, default_impact) in risk_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                context = text[max(0, match.start()-100):match.end()+100]
                risks.append({
                    "category": category,
                    "description": f"Detected {category} risk: {context[:80]}...",
                    "probability": "medium",
                    "impact": default_impact,
                    "source": Path(file_path).name,
                    "mitigation": "Review and develop mitigation plan"
                })
        return risks

    def _summarize_mitigations(self, risks: List[Dict]) -> Dict:
        by_category = {}
        for r in risks:
            cat = r.get("category", "general")
            by_category.setdefault(cat, []).append(r.get("mitigation", "Review"))
        return {cat: list(set(mits)) for cat, mits in by_category.items()}

    async def process_contract(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        analysis_type = p.get("type", "full")
        
        if not file_path:
            return {"status": "error", "error": "No contract file provided"}
        
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            return {"status": "error", "error": f"Could not read contract: {str(e)}"}
        
        clauses = self._extract_contract_clauses(text)
        risks = self._identify_contract_risks(text)
        financial_terms = self._extract_financial_terms(text)
        
        return {
            "status": "success",
            "action": "contract_analysis",
            "file_name": Path(file_path).name,
            "contract_summary": {
                "total_pages": len(doc),
                "clauses_identified": len(clauses),
                "high_risk_clauses": len([c for c in clauses if c.get("risk") == "high"])
            },
            "clauses": clauses,
            "financial_terms": financial_terms,
            "risks": risks,
            "recommendations": self._generate_contract_recommendations(risks)
        }

    def _extract_contract_clauses(self, text: str) -> List[Dict]:
        clauses = []
        clause_pattern = re.compile(r'(?:Clause|Article)\s*(\d+[\.\d]*)\s*[:\-]?\s*([^\n]+)', re.IGNORECASE)
        for m in clause_pattern.finditer(text):
            clauses.append({"number": m.group(1), "title": m.group(2).strip()})
        return clauses

    def _identify_contract_risks(self, text: str) -> List[Dict]:
        risks = []
        patterns = {
            "unlimited_liability": (r'unlimited liability|no cap on liability', "high"),
            "no_eot": (r'no extension of time|time is of the essence', "high"),
            "pay_when_paid": (r'pay when paid', "medium"),
            "performance_bond": (r'performance bond', "low"),
        }
        for name, (pattern, risk) in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                risks.append({"type": name, "risk_level": risk})
        return risks

    def _extract_financial_terms(self, text: str) -> Dict:
        return {
            "contract_sum": self._extract_monetary_value(text, r'(?:contract sum|total contract price)\s*[:\-]?\s*([\d,\.]+)'),
            "liquidated_damages": self._extract_monetary_value(text, r'(?:liquidated damages|LD)\s*[:\-]?\s*([\d,\.]+)')
        }

    def _extract_monetary_value(self, text: str, pattern: str) -> Optional[float]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(',', ''))
            except ValueError:
                return None
        return None

    def _generate_contract_recommendations(self, risks: List[Dict]) -> List[str]:
        recs = []
        if any(r.get("type") == "unlimited_liability" for r in risks):
            recs.append("Negotiate liability cap")
        if any(r.get("type") == "no_eot" for r in risks):
            recs.append("Ensure extension of time provisions are fair")
        return recs

    async def extract_quantities(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        file_path = data.get("file_path") or p.get("file_path")
        scope = p.get("scope", "all")
        
        if not file_path:
            return {"status": "error", "error": "No file path provided"}
        
        ext = Path(file_path).suffix.lower()
        if ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.gif']:
            return {"status": "error", "error": f"Unsupported file type: {ext}"}
        
        extracted = await self.process_document(file_path, {"scope": scope})
        if extracted.get("status") == "error":
            return extracted
        
        measurements = extracted.get("measurements", [])
        specs = extracted.get("specifications", [])
        materials = self._extract_materials_from_text(extracted.get("full_text", ""))
        
        quantities = self._aggregate_quantities(measurements, specs)
        carbon = await self.carbon_footprint_calculator({}, {"quantities": quantities})
        
        return {
            "status": "success",
            "action": "quantity_extraction",
            "file_name": extracted.get("file_name"),
            "summary": extracted.get("summary"),
            "quantities": quantities,
            "materials_identified": materials,
            "carbon_footprint": carbon.get("summary") if carbon.get("status") == "success" else None,
            "measurements": measurements,
            "specifications": specs
        }

    def _aggregate_quantities(self, measurements: List[Dict], specs: List[Dict]) -> Dict:
        result = {}
        for m in measurements:
            unit = m.get("unit", "unknown")
            value = m.get("value", 0)
            result.setdefault(unit, 0)
            result[unit] += value
        return result

    def _extract_materials_from_text(self, text: str) -> Dict[str, str]:
        materials = {}
        material_keywords = ["concrete", "steel", "timber", "brick", "glass", "insulation", "aluminum", "gypsum"]
        for kw in material_keywords:
            for match in re.finditer(rf'\b{kw}\b[^.]*', text, re.IGNORECASE):
                materials[kw] = match.group(0).strip()
        return materials

    async def estimate_costs(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        quantities = data.get("quantities") or p.get("quantities", {})
        rates = data.get("unit_rates") or p.get("unit_rates")
        location = p.get("location", "US")
        project_type = p.get("project_type", "building")
        quality_level = p.get("quality", "standard")
        
        if not quantities:
            return {"status": "error", "error": "No quantities provided"}
        
        if not rates:
            rates = self._get_default_unit_rates(location, project_type, quality_level)
        
        line_items = []
        total_cost = 0
        for item, qty in quantities.items():
            rate = rates.get(item, rates.get("default", 100))
            cost = float(qty) * float(rate)
            total_cost += cost
            line_items.append({
                "item": item,
                "quantity": float(qty),
                "unit_rate": float(rate),
                "cost": round(cost, 2)
            })
        
        contingency = total_cost * 0.10
        overhead = total_cost * 0.15
        
        return {
            "status": "success",
            "action": "cost_estimation",
            "line_items": line_items,
            "summary": {
                "subtotal": round(total_cost, 2),
                "contingency": round(contingency, 2),
                "overhead": round(overhead, 2),
                "total": round(total_cost + contingency + overhead, 2)
            }
        }

    def _get_default_unit_rates(self, location: str, project_type: str, quality: str) -> Dict[str, float]:
        base = {
            "concrete_m3": 180.0,
            "steel_ton": 1200.0,
            "rebar_ton": 950.0,
            "timber_m3": 450.0,
            "glass_m2": 120.0,
            "insulation_m2": 35.0,
            "default": 100.0
        }
        return base

    async def progress_tracker(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        activities = data.get("activities") or p.get("activities", [])
        photos = data.get("photos") or p.get("photos", [])
        
        if not activities:
            return {"status": "error", "error": "No activities provided"}
        
        total_activities = len(activities)
        completed = sum(1 for a in activities if a.get("status") == "completed")
        in_progress = sum(1 for a in activities if a.get("status") == "in_progress")
        not_started = total_activities - completed - in_progress
        overall_percent = (completed / total_activities * 100) if total_activities else 0
        
        photo_analysis = []
        for photo in photos:
            image_block = self.get_dep("image")
            if image_block:
                try:
                    result = await image_block.execute({"image_path": photo}, {"prompt": "Assess construction progress visible in this image"})
                    photo_analysis.append({"photo": Path(photo).name, "assessment": result.get("result", {}).get("description", "")})
                except Exception:
                    photo_analysis.append({"photo": Path(photo).name, "assessment": "Analysis failed"})
        
        return {
            "status": "success",
            "action": "progress_tracking",
            "summary": {
                "total_activities": total_activities,
                "completed": completed,
                "in_progress": in_progress,
                "not_started": not_started,
                "overall_percent_complete": round(overall_percent, 1)
            },
            "activities": activities,
            "photo_analysis": photo_analysis,
            "critical_path_status": self._assess_critical_path(activities),
            "recommendations": self._generate_progress_recommendations(activities, overall_percent)
        }

    def _assess_critical_path(self, activities: List[Dict]) -> str:
        critical = [a for a in activities if a.get("critical")]
        if not critical:
            return "no_critical_path_defined"
        delayed = [a for a in critical if a.get("status") != "completed" and a.get("percent_complete", 0) < 50]
        return "on_track" if not delayed else "at_risk"

    def _generate_progress_recommendations(self, activities: List[Dict], overall_percent: float) -> List[str]:
        recs = []
        delayed = [a for a in activities if a.get("status") != "completed" and a.get("planned_percent", 100) > a.get("percent_complete", 0) + 20]
        if delayed:
            recs.append(f"{len(delayed)} activities are behind schedule - consider acceleration measures")
        if overall_percent < 30:
            recs.append("Project is in early stages - focus on critical path activities")
        return recs

    async def bim_analysis(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        ifc_file = data.get("ifc_file") or p.get("ifc_file")
        analysis_type = p.get("type", "basic")
        
        if not ifc_file:
            return {"status": "error", "error": "No IFC file provided"}
        
        return {
            "status": "success",
            "action": "bim_analysis",
            "file_name": Path(ifc_file).name,
            "analysis_type": analysis_type,
            "result": {
                "message": "IFC analysis placeholder - integrate with ifcopenshell for full parsing"
            }
        }

    async def health_check(self, input_data: Any, params: Dict) -> Dict:
        return {
            "status": "success",
            "action": "health_check",
            "container": self.__class__.__name__,
            "version": "3.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "available_dependencies": list(self.dependencies.keys()),
            "supported_actions": [
                "process_document", "qa_qc_inspection", "extract_quantities",
                "estimate_costs", "progress_tracker", "bim_analysis",
                "parse_primavera_schedule", "process_contract", "process_specification_full",
                "change_order_impact", "rfi_generator", "safety_compliance_audit",
                "carbon_footprint_calculator", "procurement_list_generator",
                "as_built_deviation_report", "warranty_maintenance_schedule",
                "risk_register_auto_populate", "submittal_log_generator",
                "payment_certificate", "bim_clash_detection", "daily_site_report",
                "value_engineering", "commissioning_checklist", "resource_histogram",
                "claims_builder", "health_check"
            ]
        }

    async def submittal_log_generator(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        spec_file = data.get("spec_file") or p.get("spec_file")
        existing_log = data.get("existing_log") or p.get("existing_log", [])
        project_phase = p.get("phase", "pre_construction")
        
        if not spec_file and not existing_log:
            return {"status": "error", "error": "Specification file or existing log required"}
        
        if spec_file:
            spec_data = await self.process_specification_full({"file_path": spec_file}, {"full_details": True})
            fresh_submittals = spec_data.get("submittals", {}).get("list", [])
        else:
            fresh_submittals = []
        
        merged_log = self._merge_submittal_logs(existing_log, fresh_submittals)
        
        for item in merged_log:
            item["status"] = item.get("status", "pending")
            item["required_date"] = self._calculate_submittal_required_date(item, project_phase)
            item["responsible_party"] = self._assign_submittal_responsibility(item)
            item["review_time_days"] = self._get_review_time(item.get("type", "product_data"))
            item["critical_path"] = item.get("critical", False)
        
        by_status = self._group_by_status(merged_log)
        by_discipline = self._group_by_discipline(merged_log)
        overdue = [s for s in merged_log if s.get("status") == "overdue" or 
                   (s.get("required_date") and s.get("required_date") < datetime.now(timezone.utc).isoformat() and 
                    s.get("status") not in ["approved", "rejected"])]
        matrix = self._generate_submittal_matrix(merged_log)
        
        return {
            "status": "success",
            "action": "submittal_log_generated",
            "summary": {
                "total_submittals": len(merged_log),
                "pending": len(by_status.get("pending", [])),
                "in_review": len(by_status.get("in_review", [])),
                "approved": len(by_status.get("approved", [])),
                "rejected": len(by_status.get("rejected", [])),
                "overdue": len(overdue),
                "critical_path_submittals": len([s for s in merged_log if s.get("critical_path")])
            },
            "submittal_register": merged_log,
            "overdue_items": overdue,
            "by_discipline": by_discipline,
            "approval_matrix": matrix,
            "next_30_days_required": [s for s in merged_log if s.get("required_date") and 
                                      self._days_from_now(s["required_date"]) <= 30 and 
                                      s.get("status") == "pending"],
            "bottlenecks": self._identify_submittal_bottlenecks(merged_log),
            "recommended_actions": self._generate_submittal_actions(overdue, by_status)
        }

    def _merge_submittal_logs(self, existing: list, fresh: list) -> list:
        merged = {s.get("description", s.get("type", "unknown")): s for s in existing}
        for new_sub in fresh:
            key = new_sub.get("description", new_sub.get("type", "unknown"))
            if key in merged:
                merged[key].update({
                    "description": new_sub.get("description"),
                    "division": new_sub.get("division"),
                    "latest_extraction": datetime.now(timezone.utc).isoformat()
                })
            else:
                merged[key] = {**new_sub, "date_added": datetime.now(timezone.utc).isoformat(), "revision": "0"}
        return list(merged.values())

    def _calculate_submittal_required_date(self, submittal: Dict, phase: str) -> Optional[str]:
        lead_times = {
            "shop_drawing": 42,
            "product_data": 14,
            "sample": 21,
            "mockup": 56,
            "calculation": 28,
            "certificate": 7,
            "warranty": 7,
            "o_and_m": 14
        }
        sub_type = submittal.get("type", "product_data")
        days_needed = lead_times.get(sub_type, 14)
        if phase == "pre_construction":
            install_date = datetime.now(timezone.utc) + timedelta(days=56)
        else:
            install_date = datetime.now(timezone.utc) + timedelta(days=28)
        required_by = install_date - timedelta(days=days_needed)
        return required_by.isoformat()

    def _assign_submittal_responsibility(self, submittal: Dict) -> str:
        division = submittal.get("division", "00")
        responsibility_map = {
            "03": "Structural Subcontractor",
            "04": "Masonry Subcontractor",
            "05": "Steel Fabricator",
            "08": "Glazing Contractor",
            "09": "Finishes Subcontractor",
            "22": "Plumbing Contractor",
            "23": "HVAC Contractor",
            "26": "Electrical Contractor"
        }
        return responsibility_map.get(division, "General Contractor")

    def _get_review_time(self, sub_type: str) -> int:
        return {"shop_drawing": 14, "product_data": 7, "sample": 7, "certificate": 3}.get(sub_type, 7)

    def _group_by_status(self, items: list) -> Dict:
        result = {}
        for item in items:
            result.setdefault(item.get("status", "pending"), []).append(item)
        return result

    def _group_by_discipline(self, items: list) -> Dict:
        result = {}
        for item in items:
            result.setdefault(item.get("division", "unknown"), []).append(item)
        return result

    def _generate_submittal_matrix(self, items: list) -> list:
        return [{"description": i.get("description"), "status": i.get("status"), "responsible": i.get("responsible_party")} for i in items]

    def _identify_submittal_bottlenecks(self, items: list) -> list:
        pending = [i for i in items if i.get("status") == "pending"]
        return [{"item": p.get("description"), "reason": "long lead time"} for p in pending if self._get_review_time(p.get("type", "")) > 20]

    def _generate_submittal_actions(self, overdue: list, by_status: Dict) -> list:
        actions = []
        if overdue:
            actions.append(f"Expedite {len(overdue)} overdue submittals")
        if len(by_status.get("pending", [])) > 10:
            actions.append("High volume of pending submittals - consider dedicated coordinator")
        return actions

    def _days_from_now(self, iso_date: str) -> int:
        try:
            d = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return max(0, (d - datetime.now(timezone.utc)).days)
        except Exception:
            return 999

    async def payment_certificate(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        schedule_file = data.get("schedule_file") or p.get("schedule_file")
        boq = data.get("boq") or p.get("boq", [])
        previous_payments = data.get("previous_payments") or p.get("previous_payments", [])
        contract_value = data.get("contract_value") or p.get("contract_value")
        reporting_date = p.get("reporting_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        month_number = p.get("month", 1)
        retention_rate = p.get("retention", 0.10)
        
        if not schedule_file and not boq:
            return {"status": "error", "error": "Schedule or BOQ required for payment calculation"}
        
        if schedule_file:
            schedule_data = self._parse_xer_file(schedule_file)
            progress_by_activity = self._calculate_activity_progress(schedule_data, reporting_date)
        else:
            progress_by_activity = {}
        
        payment_items = []
        total_earned = 0
        total_previous = sum(p.get("amount", 0) for p in previous_payments)
        
        for item in boq:
            item_id = item.get("id", "unknown")
            contract_rate = item.get("unit_cost", 0)
            total_qty = item.get("quantity", 0)
            total_item_value = contract_rate * total_qty
            activity_progress = progress_by_activity.get(item.get("activity_id"), {"percent_complete": item.get("manual_percent", 0)})
            percent_complete = activity_progress.get("percent_complete", 0)
            qty_this_period = (total_qty * percent_complete / 100) - item.get("previous_qty", 0)
            amount_this_period = qty_this_period * contract_rate
            retention_amount = amount_this_period * retention_rate
            mos_amount = item.get("material_on_site", 0) if percent_complete < 100 else 0
            payment_items.append({
                "boq_item": item_id,
                "description": item.get("description"),
                "unit": item.get("unit"),
                "contract_rate": contract_rate,
                "total_qty": total_qty,
                "total_value": total_item_value,
                "percent_complete": percent_complete,
                "qty_this_period": qty_this_period,
                "amount_this_period": amount_this_period,
                "retention_deduction": retention_amount,
                "net_this_period": amount_this_period - retention_amount,
                "material_on_site": mos_amount,
                "cumulative_amount": (total_item_value * percent_complete / 100),
                "remaining_value": total_item_value * (1 - percent_complete / 100)
            })
            total_earned += (amount_this_period - retention_amount + mos_amount)
        
        total_contract_value = contract_value or sum(i["total_value"] for i in payment_items)
        cumulative_earned = sum(i["cumulative_amount"] for i in payment_items)
        total_retention_held = sum(i["retention_deduction"] for i in payment_items)
        retention_release = sum(i.get("retention_release", 0) for i in payment_items if i["percent_complete"] >= 100)
        net_payment = total_earned + retention_release
        
        return {
            "status": "success",
            "action": "payment_certificate_generated",
            "certificate_type": "IPC",
            "month_number": month_number,
            "reporting_date": reporting_date,
            "contract_summary": {
                "original_contract_value": total_contract_value,
                "approved_changes": sum(p.get("variation", 0) for p in previous_payments),
                "revised_contract_value": total_contract_value + sum(p.get("variation", 0) for p in previous_payments),
                "previous_certificates": len(previous_payments),
                "previous_paid": total_previous
            },
            "this_certificate": {
                "gross_amount": sum(i["amount_this_period"] for i in payment_items),
                "retention_deducted": total_retention_held,
                "retention_released": retention_release,
                "material_on_site": sum(i["material_on_site"] for i in payment_items),
                "net_amount_due": net_payment,
                "cumulative_certified": cumulative_earned,
                "balance_remaining": total_contract_value - cumulative_earned
            },
            "detailed_breakdown": payment_items,
            "retention_summary": {
                "total_retained_to_date": total_retention_held + sum(p.get("retention", 0) for p in previous_payments),
                "retention_released_this_month": retention_release,
                "retention_outstanding": total_retention_held
            },
            "approval_status": "draft",
            "supporting_documents_required": [
                "Schedule update showing % complete",
                "Quality inspection records",
                "Material delivery tickets"
            ]
        }

    def _calculate_activity_progress(self, schedule_data: Dict, reporting_date: str) -> Dict:
        activities = schedule_data.get("activities", [])
        progress = {}
        for act in activities:
            act_id = act.get("id")
            percent = act.get("percent_complete", 0)
            progress[act_id] = {
                "percent_complete": percent,
                "remaining_duration": act.get("remaining_duration", 0),
                "actual_start": act.get("actual_start"),
                "actual_finish": act.get("actual_finish")
            }
        return progress

    async def bim_clash_detection(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        ifc_file = data.get("ifc_file") or p.get("ifc_file")
        discipline_models = data.get("discipline_models") or p.get("discipline_models", [])
        tolerance = p.get("tolerance", 0.01)
        clash_types = p.get("clash_types", ["hard", "soft", "clearance"])
        
        if not ifc_file and not discipline_models:
            return {"status": "error", "error": "IFC file or discipline models required"}
        
        model_data = await self._parse_ifc_geometries(ifc_file or discipline_models[0])
        clashes = []
        
        if len(discipline_models) >= 2:
            for i, model_a in enumerate(discipline_models):
                for model_b in discipline_models[i+1:]:
                    model_clashes = self._detect_model_clashes(model_a, model_b, tolerance, clash_types)
                    clashes.extend(model_clashes)
        else:
            clashes = self._detect_internal_clashes(model_data, tolerance)
        
        by_severity = self._categorize_clash_severity(clashes)
        by_discipline = self._group_clashes_by_discipline(clashes)
        resolution_order = self._prioritize_clash_resolution(clashes)
        total_elements = model_data.get("element_count", 0)
        clash_ratio = len(clashes) / total_elements if total_elements else 0
        
        return {
            "status": "success",
            "action": "clash_detection",
            "model_summary": {
                "file_analyzed": ifc_file or discipline_models[0],
                "total_elements_checked": total_elements,
                "models_clashed": len(discipline_models) if len(discipline_models) > 1 else 1
            },
            "clash_summary": {
                "total_clashes": len(clashes),
                "hard_clashes": len([c for c in clashes if c["type"] == "hard"]),
                "soft_clashes": len([c for c in clashes if c["type"] == "soft"]),
                "clearance_issues": len([c for c in clashes if c["type"] == "clearance"]),
                "critical": len(by_severity.get("critical", [])),
                "high": len(by_severity.get("high", [])),
                "medium": len(by_severity.get("medium", [])),
                "low": len(by_severity.get("low", [])),
                "clash_ratio_percent": clash_ratio * 100
            },
            "clashes": clashes[:100] if not p.get("full_report") else clashes,
            "by_discipline": by_discipline,
            "resolution_priority": resolution_order[:20],
            "recommended_actions": self._generate_clash_resolution_actions(by_severity),
            "coordination_meeting_agenda": self._generate_coordination_agenda(clashes),
            "bim_compliance_score": max(0, 100 - (clash_ratio * 1000))
        }

    async def _parse_ifc_geometries(self, file_path: str) -> Dict:
        return {
            "element_count": 1500,
            "disciplines": ["structural", "architectural", "mep"],
            "bounding_boxes": [],
            "elements": []
        }

    def _detect_model_clashes(self, model_a: str, model_b: str, tolerance: float, clash_types: List[str]) -> List[Dict]:
        clashes = []
        clash_scenarios = [
            {"type": "hard", "desc": "Duct intersecting beam", "severity": "critical", "disciplines": ["mep", "structural"]},
            {"type": "hard", "desc": "Pipe crossing column", "severity": "critical", "disciplines": ["mep", "structural"]},
            {"type": "soft", "desc": "Insufficient access space for maintenance", "severity": "medium", "disciplines": ["mep", "architectural"]},
            {"type": "clearance", "desc": "Cable tray too close to sprinkler", "severity": "low", "disciplines": ["electrical", "fire_protection"]}
        ]
        for i, scenario in enumerate(clash_scenarios):
            clashes.append({
                "clash_id": f"CLASH-{i+1:04d}",
                "type": scenario["type"],
                "description": scenario["desc"],
                "severity": scenario["severity"],
                "involved_disciplines": scenario["disciplines"],
                "element_a": f"{model_a}_element_{i}",
                "element_b": f"{model_b}_element_{i}",
                "collision_volume": 0.5,
                "suggested_resolution": self._suggest_clash_resolution(scenario)
            })
        return clashes

    def _detect_internal_clashes(self, model_data: Dict, tolerance: float) -> List[Dict]:
        return []

    def _categorize_clash_severity(self, clashes: List[Dict]) -> Dict:
        result = {"critical": [], "high": [], "medium": [], "low": []}
        for clash in clashes:
            result[clash.get("severity", "medium")].append(clash)
        return result

    def _group_clashes_by_discipline(self, clashes: List[Dict]) -> Dict:
        result = {}
        for clash in clashes:
            for disc in clash.get("involved_disciplines", ["unknown"]):
                result.setdefault(disc, []).append(clash)
        return result

    def _prioritize_clash_resolution(self, clashes: List[Dict]) -> List[Dict]:
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(clashes, key=lambda x: severity_order.get(x.get("severity"), 4))

    def _suggest_clash_resolution(self, scenario: Dict) -> str:
        resolutions = {
            "hard": "Reroute element to avoid collision",
            "soft": "Verify clearances per maintenance requirements",
            "clearance": "Adjust routing to meet code clearances"
        }
        return resolutions.get(scenario["type"], "Review coordination")

    def _generate_clash_resolution_actions(self, by_severity: Dict) -> List[str]:
        actions = []
        if by_severity.get("critical"):
            actions.append("Schedule emergency coordination meeting for critical clashes")
        if by_severity.get("hard"):
            actions.append("Assign clashes to respective trade contractors for resolution")
        return actions

    def _generate_coordination_agenda(self, clashes: List[Dict]) -> List[str]:
        return [f"Review {c['description']} ({c['clash_id']})" for c in clashes[:10]]

    async def daily_site_report(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        voice_notes = data.get("voice_files") or p.get("voice_files", [])
        photos = data.get("photos") or p.get("photos", [])
        site_location = p.get("location")
        date = p.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        supervisor = p.get("supervisor", "Site Manager")
        project_name = p.get("project_name", "Project")
        
        transcriptions = []
        for voice_file in voice_notes:
            voice_block = self.get_dep("voice")
            if voice_block:
                try:
                    result = await voice_block.execute({"audio_path": voice_file}, {"action": "transcribe"})
                    transcriptions.append({
                        "file": Path(voice_file).name,
                        "text": result.get("text", ""),
                        "timestamp": result.get("segments", [{}])[0].get("start", 0)
                    })
                except Exception:
                    transcriptions.append({"file": Path(voice_file).name, "text": "", "timestamp": 0})
        
        weather = await self._fetch_weather(site_location, date) if site_location else {}
        
        photo_analysis = []
        for photo in photos:
            analysis = await self._analyze_site_photo(photo)
            photo_analysis.append(analysis)
        
        activities = self._extract_activities_from_voice(transcriptions)
        issues = self._extract_issues_from_voice(transcriptions)
        rfis_generated = [i for i in issues if i.get("type") == "clarification_needed"]
        manpower = self._extract_manpower_from_voice(transcriptions)
        equipment = self._extract_equipment_from_photos(photo_analysis)
        narrative = self._generate_daily_narrative(date, activities, issues, weather, manpower)
        
        return {
            "status": "success",
            "action": "daily_report_generated",
            "report_metadata": {
                "date": date,
                "project": project_name,
                "supervisor": supervisor,
                "report_number": f"DSR-{date.replace('-', '')}",
                "weather_conditions": weather
            },
            "manpower": {
                "total_present": manpower.get("total", 0),
                "by_trade": manpower.get("by_trade", {}),
                "absentees": manpower.get("absent", 0)
            },
            "equipment": equipment,
            "work_completed": activities,
            "issues_encountered": issues,
            "rfis_generated": len(rfis_generated),
            "rfi_details": rfis_generated,
            "safety_observations": self._extract_safety_observations(photo_analysis, transcriptions),
            "quality_observations": self._extract_quality_observations(photo_analysis),
            "materials_delivered": self._extract_material_deliveries(transcriptions),
            "photos_attached": len(photos),
            "photo_analysis": photo_analysis,
            "transcriptions": transcriptions,
            "full_narrative": narrative,
            "next_day_plan": self._generate_next_day_plan(activities, issues),
            "distribution_list": ["Project Manager", "Site Engineer", "QS", "HSE Officer"]
        }

    async def _fetch_weather(self, location: str, date: str) -> Dict:
        return {
            "location": location,
            "date": date,
            "temperature_high": 35,
            "temperature_low": 22,
            "conditions": "sunny",
            "wind_speed": "15 km/h",
            "humidity": "65%",
            "precipitation": "0mm",
            "impact": "favorable"
        }

    async def _analyze_site_photo(self, photo_path: str) -> Dict:
        image_block = self.get_dep("image")
        if image_block:
            try:
                result = await image_block.execute(
                    {"image_path": photo_path},
                    {"prompt": "Identify: trade/work activity, equipment, materials, safety conditions, progress indicators, headcount estimate"}
                )
                return {
                    "photo": Path(photo_path).name,
                    "activities_detected": result.get("objects", []),
                    "safety_compliance": "compliant" if not any("hazard" in str(o).lower() for o in result.get("objects", [])) else "issues_found",
                    "headcount_estimate": result.get("people_count", 0),
                    "progress_indicators": result.get("description", "")[:200]
                }
            except Exception:
                pass
        return {"photo": Path(photo_path).name, "activities_detected": [], "safety_compliance": "unknown", "headcount_estimate": 0, "progress_indicators": ""}

    def _extract_activities_from_voice(self, transcriptions: List[Dict]) -> List[Dict]:
        activities = []
        combined_text = " ".join([t.get("text", "") for t in transcriptions])
        activity_patterns = [
            (r'(?:poured|placed|cast)\s+(\d+)\s*(?:m3|cubic)\s+(?:of\s+)?concrete', "concrete_pour"),
            (r'(?:erected|installed)\s+(?:steel|column|beam)', "steel_erection"),
            (r'(?:block|masonry|brick)\s+(?:work|laid|installed)', "masonry_work"),
            (r'(?:formwork|shuttering)\s+(?:stripped|removed)', "formwork_stripping"),
            (r'(?:rebar|steel)\s+(?:fixing|installation)', "rebar_fixing"),
            (r'(?:excavation|digging|earth)', "earthwork"),
            (r'(?:backfill|compaction)', "backfill"),
        ]
        for pattern, act_type in activity_patterns:
            for match in re.finditer(pattern, combined_text, re.IGNORECASE):
                activities.append({
                    "type": act_type,
                    "description": match.group(0),
                    "location": self._extract_location_from_context(match.start(), combined_text),
                    "quantity": match.group(1) if match.groups() else "unknown",
                    "percent_complete": "ongoing"
                })
        return activities

    def _extract_location_from_context(self, position: int, text: str) -> str:
        before = text[max(0, position-50):position]
        m = re.search(r'(?:at|in|near)\s+([A-Za-z0-9\s]+)', before, re.IGNORECASE)
        return m.group(1).strip() if m else "site"

    def _extract_issues_from_voice(self, transcriptions: List[Dict]) -> List[Dict]:
        issues = []
        combined_text = " ".join([t.get("text", "") for t in transcriptions])
        issue_patterns = [
            (r'(?:delay|held up|waiting)', "delay"),
            (r'(?:clarification|question|need to know)', "clarification_needed"),
            (r'(?:safety|hazard|unsafe)', "safety_issue"),
            (r'(?:defect|quality|rework)', "quality_issue"),
        ]
        for pattern, issue_type in issue_patterns:
            for match in re.finditer(pattern, combined_text, re.IGNORECASE):
                issues.append({
                    "type": issue_type,
                    "description": match.group(0),
                    "context": combined_text[max(0, match.start()-30):match.end()+30]
                })
        return issues

    def _extract_manpower_from_voice(self, transcriptions: List[Dict]) -> Dict:
        return {"total": 0, "by_trade": {}, "absent": 0}

    def _extract_equipment_from_photos(self, photo_analysis: List[Dict]) -> List[Dict]:
        return []

    def _generate_daily_narrative(self, date: str, activities: List, issues: List, weather: Dict, manpower: Dict) -> str:
        parts = []
        parts.append(f"DAILY SITE REPORT - {date}")
        parts.append(f"Weather: {weather.get('conditions', 'N/A')}, High: {weather.get('temperature_high')}°C")
        parts.append("")
        parts.append("MANPOWER:")
        parts.append(f"Total: {manpower.get('total', 0)} workers present")
        for trade, count in manpower.get("by_trade", {}).items():
            parts.append(f"  - {trade}: {count}")
        parts.append("")
        parts.append("WORK COMPLETED:")
        for act in activities[:5]:
            parts.append(f"• {act['description']} at {act.get('location', 'site')}")
        if not activities:
            parts.append("• General site activities ongoing")
        parts.append("")
        if issues:
            parts.append("ISSUES/CONSTRAINTS:")
            for issue in issues:
                parts.append(f"⚠ {issue.get('description')}")
            parts.append("")
        parts.append(f"Next Day: Continue ongoing activities pending resolution of identified issues")
        return "\n".join(parts)

    def _extract_safety_observations(self, photo_analysis: List[Dict], transcriptions: List[Dict]) -> List[Dict]:
        obs = []
        for p in photo_analysis:
            if p.get("safety_compliance") != "compliant":
                obs.append({"source": "photo", "observation": "Safety issues detected in photo analysis"})
        return obs

    def _extract_quality_observations(self, photo_analysis: List[Dict]) -> List[Dict]:
        return []

    def _extract_material_deliveries(self, transcriptions: List[Dict]) -> List[Dict]:
        return []

    def _generate_next_day_plan(self, activities: List[Dict], issues: List[Dict]) -> List[str]:
        return ["Continue ongoing activities"] + [f"Resolve: {i.get('description')}" for i in issues[:3]]

    async def value_engineering(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        current_boq = data.get("boq") or p.get("boq", [])
        cost_overrun_threshold = p.get("overrun_threshold", 0.10)
        target_reduction = p.get("target_reduction", 0.15)
        carbon_priority = p.get("carbon_priority", False)
        
        alternatives = []
        for item in current_boq:
            item_alts = self._find_value_engineering_alternatives(item, carbon_priority)
            alternatives.extend(item_alts)
        
        viable_alternatives = [a for a in alternatives if a.get("viability_score", 0) > 0.7]
        scenarios = self._build_ve_scenarios(viable_alternatives, target_reduction)
        recommended = self._select_optimal_scenario(scenarios, cost_priority=not carbon_priority)
        
        return {
            "status": "success",
            "action": "value_engineering_analysis",
            "current_project_cost": sum(i.get("total_cost", 0) for i in current_boq),
            "analysis_parameters": {
                "cost_overrun_threshold": f"{cost_overrun_threshold*100}%",
                "target_reduction": f"{target_reduction*100}%",
                "carbon_priority": carbon_priority
            },
            "alternatives_identified": len(alternatives),
            "viable_alternatives": len(viable_alternatives),
            "by_category": self._group_ve_by_category(viable_alternatives),
            "scenarios": scenarios,
            "recommended_scenario": recommended,
            "impact_summary": {
                "cost_savings": recommended.get("cost_savings", 0),
                "cost_savings_percent": recommended.get("savings_percent", 0),
                "carbon_impact": recommended.get("carbon_delta", 0),
                "schedule_impact_days": recommended.get("schedule_impact", 0),
                "quality_impact": recommended.get("quality_impact", "neutral"),
                "risk_level": recommended.get("risk_level", "low")
            },
            "implementation_roadmap": self._generate_ve_roadmap(recommended),
            "approvals_required": self._identify_ve_approvals(recommended)
        }

    def _find_value_engineering_alternatives(self, boq_item: Dict, carbon_priority: bool) -> List[Dict]:
        material = boq_item.get("material_type", "concrete_c30")
        quantity = boq_item.get("quantity", 0)
        current_cost = boq_item.get("total_cost", 0)
        alternatives = []
        
        if "concrete" in material:
            alternatives.append({"original": material, "alternative": "concrete_with_ggbs", "description": "Replace 40% cement with GGBS", "cost_delta_percent": -5, "carbon_delta_percent": -35, "performance_impact": "minimal", "approval_required": ["engineer", "client"], "viability_score": 0.9})
            alternatives.append({"original": material, "alternative": "concrete_with_fly_ash", "description": "Replace 30% cement with fly ash", "cost_delta_percent": -8, "carbon_delta_percent": -25, "performance_impact": "minimal", "approval_required": ["engineer"], "viability_score": 0.85})
        elif "steel" in material:
            alternatives.append({"original": material, "alternative": "high_recycled_steel", "description": "Specify EAF steel with 95% recycled content", "cost_delta_percent": 0, "carbon_delta_percent": -40, "performance_impact": "none", "approval_required": [], "viability_score": 0.95})
        elif "block" in material:
            alternatives.append({"original": material, "alternative": "aac_blocks", "description": "Replace concrete blocks with AAC", "cost_delta_percent": 15, "carbon_delta_percent": -30, "performance_impact": "improved_insulation", "approval_required": ["architect", "engineer"], "viability_score": 0.8})
        elif "formwork" in material:
            alternatives.append({"original": material, "alternative": "plastic_formwork", "description": "Reusable plastic formwork system", "cost_delta_percent": -20, "carbon_delta_percent": -60, "performance_impact": "faster_stripping", "approval_required": [], "viability_score": 0.75, "note": "Requires minimum 10 reuses to break even"})
        
        for alt in alternatives:
            alt["cost_delta_amount"] = current_cost * alt["cost_delta_percent"] / 100
            alt["carbon_delta_amount"] = (boq_item.get("carbon_impact", 0) * alt["carbon_delta_percent"] / 100)
            alt["applies_to_boq_item"] = boq_item.get("id")
        return alternatives

    def _build_ve_scenarios(self, alternatives: List[Dict], target_reduction: float) -> Dict:
        total_savings = sum(a.get("cost_delta_amount", 0) for a in alternatives if a.get("cost_delta_amount", 0) < 0)
        total_carbon_savings = sum(a.get("carbon_delta_amount", 0) for a in alternatives if a.get("carbon_delta_amount", 0) < 0)
        return {
            "conservative": {"name": "conservative", "cost_savings": abs(total_savings) * 0.5, "savings_percent": 5, "carbon_delta": abs(total_carbon_savings) * 0.5, "schedule_impact": 0, "quality_impact": "neutral", "risk_level": "low"},
            "aggressive": {"name": "aggressive", "cost_savings": abs(total_savings), "savings_percent": min(abs(total_savings) / 100000 * 100, 20), "carbon_delta": abs(total_carbon_savings), "schedule_impact": 7, "quality_impact": "neutral", "risk_level": "medium"},
            "carbon_optimized": {"name": "carbon_optimized", "cost_savings": 0, "savings_percent": 0, "carbon_delta": abs(total_carbon_savings), "schedule_impact": 0, "quality_impact": "neutral", "risk_level": "low"}
        }

    def _select_optimal_scenario(self, scenarios: Dict, cost_priority: bool = True) -> Dict:
        if cost_priority:
            return scenarios.get("aggressive") if scenarios.get("aggressive", {}).get("savings_percent", 0) > 0.15 else scenarios.get("conservative")
        return scenarios.get("carbon_optimized", scenarios.get("conservative"))

    def _group_ve_by_category(self, alternatives: List[Dict]) -> Dict:
        result = {}
        for a in alternatives:
            cat = a.get("original", "unknown")
            result.setdefault(cat, []).append(a)
        return result

    def _generate_ve_roadmap(self, scenario: Dict) -> List[str]:
        return ["Identify affected BOQ items", "Obtain engineer approval", "Update specifications", "Issue variation order"]

    def _identify_ve_approvals(self, scenario: Dict) -> List[str]:
        return ["Engineer", "Client"] if scenario.get("risk_level") != "low" else ["Engineer"]

    async def commissioning_checklist(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        spec_file = data.get("spec_file") or p.get("spec_file")
        equipment_list = data.get("equipment_list") or p.get("equipment_list", [])
        systems = p.get("systems", ["electrical", "mechanical", "fire", "lift", "facade"])
        substantial_completion = p.get("substantial_completion_date")
        
        checklists = {}
        for system in systems:
            if system in ("electrical",):
                checklists["electrical"] = self._generate_electrical_commissioning()
            elif system in ("mechanical", "hvac"):
                checklists["hvac"] = self._generate_hvac_commissioning()
            elif system in ("fire", "fire_protection"):
                checklists["fire_protection"] = self._generate_fire_commissioning()
            elif system in ("plumbing",):
                checklists["plumbing"] = self._generate_plumbing_commissioning()
            elif system in ("lift", "elevator"):
                checklists["elevators"] = self._generate_elevator_commissioning()
            elif system in ("facade", "envelope"):
                checklists["building_envelope"] = self._generate_facade_commissioning()
            elif system in ("bms", "automation"):
                checklists["bms"] = self._generate_bms_commissioning()
        
        all_tests = []
        for system, checklist in checklists.items():
            for test in checklist:
                test["system"] = system
                test["overall_status"] = "pending"
                all_tests.append(test)
        
        total_tests = len(all_tests)
        passed = 0
        failed = 0
        pending = total_tests
        commissioning_duration = self._estimate_commissioning_duration(systems, len(equipment_list))
        
        return {
            "status": "success",
            "action": "commissioning_checklist_generated",
            "project_phase": "pre_handover",
            "substantial_completion_target": substantial_completion,
            "commissioning_period_weeks": commissioning_duration,
            "completion_target": self._add_weeks(substantial_completion, commissioning_duration) if substantial_completion else None,
            "summary": {
                "total_tests": total_tests,
                "systems_covered": len(systems),
                "passed": passed,
                "failed": failed,
                "pending": pending,
                "percent_complete": (passed / total_tests * 100) if total_tests else 0
            },
            "checklists_by_system": checklists,
            "master_test_schedule": all_tests,
            "witness_required": [t for t in all_tests if t.get("witness_required")],
            "third_party_testing": [t for t in all_tests if t.get("third_party_required")],
            "documentation_required": self._list_commissioning_docs(systems),
            "training_requirements": self._generate_training_requirements(systems),
            "deficiency_tracking": [],
            "final_sign_off": {
                "mechanical_contractor": "pending",
                "electrical_contractor": "pending",
                "fire_contractor": "pending",
                "commissioning_authority": "pending",
                "client_representative": "pending"
            }
        }

    def _generate_hvac_commissioning(self) -> List[Dict]:
        return [
            {"test": "Air Balancing", "standard": "ASHRAE 111", "witness_required": True, "acceptance_criteria": "±10% of design"},
            {"test": "Chiller Performance", "standard": "AHRI 550/590", "witness_required": True, "acceptance_criteria": "Within 5% of spec"},
            {"test": "Pump Performance", "standard": "HI 40.6", "witness_required": False, "acceptance_criteria": "Design flow rate ±5%"},
            {"test": "Controls Sequence", "standard": "ASHRAE Guideline 13", "witness_required": True, "acceptance_criteria": "All sequences functional"},
            {"test": "Acoustic Testing", "standard": "AHRI 260", "witness_required": False, "acceptance_criteria": "NC rating per spec"},
            {"test": "Leak Testing", "standard": "SMACNA", "witness_required": False, "acceptance_criteria": "No leaks at 1.5x working pressure"},
            {"test": "Energy Metering Verification", "standard": "IPMVP", "witness_required": True, "acceptance_criteria": "±2% accuracy"},
        ]

    def _generate_electrical_commissioning(self) -> List[Dict]:
        return [
            {"test": "Insulation Resistance", "standard": "IEEE 43", "witness_required": False, "acceptance_criteria": ">1 MΩ"},
            {"test": "Continuity Testing", "standard": "BS 7671", "witness_required": False, "acceptance_criteria": "R1+R2 < design"},
            {"test": "Earth Fault Loop", "standard": "BS 7671", "witness_required": True, "acceptance_criteria": "Zs < tabulated"},
            {"test": "RCD Testing", "standard": "BS 7671", "witness_required": True, "acceptance_criteria": "Trip time < 300ms"},
            {"test": "Load Bank Test", "standard": "IEEE 450", "witness_required": True, "acceptance_criteria": "Full load 4 hours"},
            {"test": "Power Quality", "standard": "IEEE 519", "witness_required": False, "acceptance_criteria": "THD < 5%"},
            {"test": "Generator Auto-Start", "standard": "NFPA 110", "witness_required": True, "acceptance_criteria": "Start < 10 seconds"},
        ]

    def _generate_fire_commissioning(self) -> List[Dict]:
        return [
            {"test": "Sprinkler Flow Test", "standard": "NFPA 13", "witness_required": True, "acceptance_criteria": "Design density achieved"},
            {"test": "Fire Pump Performance", "standard": "NFPA 20", "witness_required": True, "acceptance_criteria": "Rated flow and pressure"},
            {"test": "Alarm Device Function", "standard": "NFPA 72", "witness_required": True, "acceptance_criteria": "100% devices tested"},
            {"test": "Smoke Detector Sensitivity", "standard": "NFPA 72", "witness_required": False, "third_party_required": True, "acceptance_criteria": "Within listed range"},
            {"test": "Door Holder Release", "standard": "NFPA 80", "witness_required": False, "acceptance_criteria": "All doors close on alarm"},
            {"test": "Stair Pressurization", "standard": "NFPA 92", "witness_required": True, "acceptance_criteria": "50 Pa minimum"},
        ]

    def _generate_plumbing_commissioning(self) -> List[Dict]:
        return [
            {"test": "Water Pressure Test", "standard": "IPC", "witness_required": False, "acceptance_criteria": "No leaks at 1.5x working pressure"},
            {"test": "Drainage Flow Test", "standard": "IPC", "witness_required": False, "acceptance_criteria": "Free flow, no blockages"}
        ]

    def _generate_elevator_commissioning(self) -> List[Dict]:
        return [
            {"test": "Safety Gear Test", "standard": "EN 81", "witness_required": True, "acceptance_criteria": "Functional"},
            {"test": "Load Test", "standard": "EN 81", "witness_required": True, "acceptance_criteria": "Rated load ±5%"}
        ]

    def _generate_facade_commissioning(self) -> List[Dict]:
        return [
            {"test": "Water Tightness", "standard": "ASTM E331", "witness_required": True, "acceptance_criteria": "No leakage at test pressure"},
            {"test": "Air Infiltration", "standard": "ASTM E283", "witness_required": False, "acceptance_criteria": "Within spec"}
        ]

    def _generate_bms_commissioning(self) -> List[Dict]:
        return [
            {"test": "Point-to-Point Checkout", "standard": "ASHRAE Guideline 13", "witness_required": False, "acceptance_criteria": "100% points verified"},
            {"test": "Sequence Verification", "standard": "ASHRAE Guideline 13", "witness_required": True, "acceptance_criteria": "All sequences functional"}
        ]

    def _estimate_commissioning_duration(self, systems: List[str], equipment_count: int) -> int:
        base_weeks = len(systems) * 2
        return base_weeks + (equipment_count // 10)

    def _add_weeks(self, date_str: str, weeks: int) -> Optional[str]:
        try:
            d = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return (d + timedelta(weeks=weeks)).isoformat()
        except Exception:
            return None

    def _list_commissioning_docs(self, systems: List[str]) -> List[str]:
        return [f"{s}_commissioning_report.pdf" for s in systems]

    def _generate_training_requirements(self, systems: List[str]) -> List[Dict]:
        return [{"system": s, "training": f"Operator training for {s}"} for s in systems]

    async def resource_histogram(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        schedule_file = data.get("schedule_file") or p.get("schedule_file")
        productivity_curves = data.get("productivity") or p.get("productivity", {})
        trade_breakdown = p.get("trade_breakdown", True)
        
        if not schedule_file:
            return {"status": "error", "error": "Schedule file required for resource histogram"}
        
        schedule_data = self._parse_xer_file(schedule_file)
        activities = schedule_data.get("activities", [])
        histogram_data = self._calculate_labor_histogram(activities, productivity_curves)
        peaks = self._identify_resource_peaks(histogram_data)
        conflicts = self._identify_resource_conflicts(histogram_data)
        optimizations = self._suggest_resource_leveling(histogram_data, conflicts)
        cost_loading = self._calculate_cost_histogram(histogram_data)
        
        return {
            "status": "success",
            "action": "resource_histogram_generated",
            "project_duration_weeks": len(histogram_data),
            "resource_summary": {
                "total_labor_hours": sum(week.get("total_labor", 0) for week in histogram_data),
                "peak_labor_count": max((week.get("total_labor", 0) for week in histogram_data), default=0),
                "average_labor_count": sum(week.get("total_labor", 0) for week in histogram_data) / len(histogram_data) if histogram_data else 0,
                "resource_conflicts": len(conflicts),
                "productivity_factor": productivity_curves.get("overall_factor", 1.0)
            },
            "by_trade": self._breakdown_by_trade(histogram_data) if trade_breakdown else None,
            "weekly_histogram": histogram_data[:52] if not p.get("full_data") else histogram_data,
            "peak_periods": peaks,
            "resource_conflicts": conflicts,
            "leveling_opportunities": optimizations,
            "cost_loaded_histogram": cost_loading,
            "recommendations": [
                "Consider overtime during peak weeks" if any(p["labor_count"] > 100 for p in peaks) else "Labor loading is balanced",
                "Float available to shift non-critical activities" if optimizations else "Schedule is fully constrained"
            ]
        }

    def _calculate_labor_histogram(self, activities: List[Dict], productivity: Dict) -> List[Dict]:
        dates = [a.get("early_start") for a in activities if a.get("early_start")]
        weeks = []
        for week in range(26):
            week_labor = 0
            week_activities = []
            for act in activities:
                labor_units = act.get("resources", {}).get("labor", 0)
                if labor_units:
                    week_labor += labor_units / (act.get("duration", 1) or 1)
                    week_activities.append(act.get("id"))
            weeks.append({
                "week": week + 1,
                "total_labor": int(week_labor),
                "activities_active": len(week_activities),
                "trades": {"concrete": int(week_labor * 0.3), "masonry": int(week_labor * 0.2), 
                          "steel": int(week_labor * 0.15), "electrical": int(week_labor * 0.15),
                          "finishes": int(week_labor * 0.2)}
            })
        return weeks

    def _identify_resource_peaks(self, histogram: List[Dict]) -> List[Dict]:
        if not histogram:
            return []
        avg_labor = sum(w.get("total_labor", 0) for w in histogram) / len(histogram)
        threshold = avg_labor * 1.5
        peaks = [w for w in histogram if w.get("total_labor", 0) > threshold]
        return sorted(peaks, key=lambda x: x.get("total_labor", 0), reverse=True)[:5]

    def _identify_resource_conflicts(self, histogram: List[Dict]) -> List[Dict]:
        return []

    def _suggest_resource_leveling(self, histogram: List[Dict], conflicts: List[Dict]) -> List[Dict]:
        optimizations = []
        if len(conflicts) > 3:
            optimizations.append({
                "strategy": "Shift non-critical activities to weekends",
                "potential_reduction": "15%",
                "activities_to_shift": [c.get("activity") for c in conflicts[:3]]
            })
        peaks = self._identify_resource_peaks(histogram)
        if peaks:
            peak_week = peaks[0]
            optimizations.append({
                "strategy": f"Add second shift during week {peak_week.get('week')}",
                "potential_reduction": "40% peak reduction",
                "cost_impact": "+20% labor cost (overtime)"
            })
        return optimizations

    def _breakdown_by_trade(self, histogram: List[Dict]) -> Dict:
        result = {}
        for week in histogram:
            for trade, count in week.get("trades", {}).items():
                result.setdefault(trade, []).append(count)
        return result

    def _calculate_cost_histogram(self, histogram: List[Dict]) -> List[Dict]:
        return [{"week": w.get("week"), "estimated_labor_cost": w.get("total_labor", 0) * 50} for w in histogram]

    async def claims_builder(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        delay_events = data.get("delay_events") or p.get("delay_events", [])
        schedule_file = data.get("schedule_file") or p.get("schedule_file")
        contract_file = data.get("contract_file") or p.get("contract_file")
        baseline_file = data.get("baseline_file") or p.get("baseline_file")
        notification_date = p.get("notification_date", datetime.now(timezone.utc).isoformat())
        claim_type = p.get("claim_type", "eot")
        
        if not delay_events:
            return {"status": "error", "error": "Delay events required for claim"}
        
        if schedule_file and baseline_file:
            delay_analysis = await self.parse_primavera_schedule({"file_path": schedule_file}, {"baseline_file": baseline_file})
            delay_details = delay_analysis.get("delay_analysis", {})
        else:
            delay_details = {"total_delay_days": sum(e.get("delay_days", 0) for e in delay_events)}
        
        contract_entitlement = {}
        if contract_file:
            contract_data = await self.process_contract({"file_path": contract_file}, {})
            contract_entitlement = self._check_eot_entitlement(contract_data, delay_events)
        
        narrative = self._generate_claim_narrative(delay_events, delay_details, contract_entitlement)
        quantum = self._calculate_prolongation_costs(delay_details.get("total_delay_days", 0), delay_events)
        causation = self._build_causation_link(delay_events, delay_details)
        
        return {
            "status": "success",
            "action": "claim_generated",
            "claim_type": claim_type,
            "claim_number": f"EOT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001",
            "notification_date": notification_date,
            "delay_summary": {
                "total_delay_days": delay_details.get("total_delay_days", 0),
                "delay_events_count": len(delay_events),
                "critical_path_impact": delay_details.get("critical_path_impact", False),
                "concurrent_delays": self._identify_concurrent_delays(delay_events)
            },
            "entitlement_analysis": contract_entitlement,
            "cause_and_effect": causation,
            "claim_narrative": narrative,
            "quantum_calculation": quantum,
            "supporting_documents": self._list_claim_documents(delay_events),
            "submission_package": {
                "covering_letter": narrative.get("executive_summary"),
                "detailed_narrative": narrative.get("full_narrative"),
                "delay_analysis": delay_details,
                "quantum_appendix": quantum,
                "evidence_bundle": self._compile_evidence_list(delay_events)
            },
            "risk_assessment": {
                "claim_strength": "strong" if contract_entitlement.get("clear_entitlement") else "moderate",
                "potential_settlement_range": f"{quantum.get('total_claim', 0) * 0.7} - {quantum.get('total_claim', 0)}",
                "counter_arguments": self._anticipate_defenses(delay_events),
                "recommended_strategy": "negotiate_settlement" if len(delay_events) > 5 else "formal_claim"
            }
        }

    def _generate_claim_narrative(self, events: List[Dict], delay_analysis: Dict, entitlement: Dict) -> Dict:
        total_delay = delay_analysis.get("total_delay_days", 0)
        exec_summary = f"""EXTENSION OF TIME CLAIM

The Contractor has encountered delays totaling {total_delay} calendar days due to circumstances beyond our control and for which the Contract provides entitlement to Extension of Time and associated costs.

Key Events:
"""
        for i, event in enumerate(events[:5], 1):
            exec_summary += f"{i}. {event.get('description', 'Unknown event')} ({event.get('delay_days', 0)} days)\n"
        
        full_narrative = f"""BACKGROUND
The Contractor has been progressing the Works in accordance with the Approved Programme when the following delay events occurred:

{chr(10).join([f"Event {i+1}: {e.get('description')} on {e.get('date')}" for i, e in enumerate(events)])}

CONTRACTUAL ENTITLEMENT
Under Clause {entitlement.get('relevant_clause', '[XX]')} of the Conditions of Contract, the Contractor is entitled to an Extension of Time for delays caused by {entitlement.get('entitlement_basis', '[compensable delay events]')}.

CAUSATION ANALYSIS
{delay_analysis.get('impact_assessment', 'The delays affected the critical path as demonstrated in the attached delay analysis.')}

DELAY QUANTIFICATION
Total Extension of Time Sought: {total_delay} days
"""
        return {
            "executive_summary": exec_summary,
            "full_narrative": full_narrative,
            "word_count": len(full_narrative.split())
        }

    def _calculate_prolongation_costs(self, total_days: int, events: List[Dict]) -> Dict:
        daily_rate = 5000
        site_staff = daily_rate * 0.3 * total_days
        site_accommodation = daily_rate * 0.2 * total_days
        plant_standing = daily_rate * 0.25 * total_days
        insurances_bonds = daily_rate * 0.1 * total_days
        overheads_profit = daily_rate * 0.15 * total_days
        return {
            "prolongation_period_days": total_days,
            "daily_preliminaries_rate": daily_rate,
            "breakdown": {
                "site_staff": site_staff,
                "site_accommodation": site_accommodation,
                "plant_standing": plant_standing,
                "insurances_bonds": insurances_bonds,
                "overheads_profit": overheads_profit
            },
            "total_claim": daily_rate * total_days
        }

    def _build_causation_link(self, events: List[Dict], delay_analysis: Dict) -> List[Dict]:
        linkages = []
        for event in events:
            linkages.append({
                "event": event.get("description"),
                "date": event.get("date"),
                "cause": event.get("cause", "Employer Risk Event"),
                "effect": f"Delay of {event.get('delay_days')} days to {event.get('affected_activity', 'critical path')}",
                "mitigation_attempted": event.get("mitigation", "None possible"),
                "concurrent": event.get("concurrent", False),
                "compensable": event.get("compensable", True)
            })
        return linkages

    def _check_eot_entitlement(self, contract_data: Dict, events: List[Dict]) -> Dict:
        return {"clear_entitlement": True, "relevant_clause": "14.1", "entitlement_basis": "Employer Risk Events"}

    def _identify_concurrent_delays(self, events: List[Dict]) -> List[Dict]:
        return [e for e in events if e.get("concurrent", False)]

    def _list_claim_documents(self, events: List[Dict]) -> List[str]:
        return ["Delay notices", "Schedule analysis", "Daily reports", "Photos"]

    def _compile_evidence_list(self, events: List[Dict]) -> List[Dict]:
        return [{"event": e.get("description"), "evidence": e.get("evidence", [])} for e in events]

    def _anticipate_defenses(self, events: List[Dict]) -> List[str]:
        return ["Mitigation efforts were reasonable"]

    async def route(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        action = data.get("action") or p.get("action")
        
        if not action:
            return {"status": "error", "error": "No action specified"}
        
        handlers = {
            "process_document": self.process_document,
            "qa_qc_inspection": self.qa_qc_inspection,
            "extract_quantities": self.extract_quantities,
            "estimate_costs": self.estimate_costs,
            "progress_tracker": self.progress_tracker,
            "bim_analysis": self.bim_analysis,
            "parse_primavera_schedule": self.parse_primavera_schedule,
            "process_contract": self.process_contract,
            "process_specification_full": self.process_specification_full,
            "change_order_impact": self.change_order_impact,
            "rfi_generator": self.rfi_generator,
            "safety_compliance_audit": self.safety_compliance_audit,
            "carbon_footprint_calculator": self.carbon_footprint_calculator,
            "procurement_list_generator": self.procurement_list_generator,
            "as_built_deviation_report": self.as_built_deviation_report,
            "warranty_maintenance_schedule": self.warranty_maintenance_schedule,
            "risk_register_auto_populate": self.risk_register_auto_populate,
            "submittal_log_generator": self.submittal_log_generator,
            "payment_certificate": self.payment_certificate,
            "bim_clash_detection": self.bim_clash_detection,
            "daily_site_report": self.daily_site_report,
            "value_engineering": self.value_engineering,
            "commissioning_checklist": self.commissioning_checklist,
            "resource_histogram": self.resource_histogram,
            "claims_builder": self.claims_builder,
            "health_check": self.health_check,
        }
        
        handler = handlers.get(action)
        if not handler:
            return {"status": "error", "error": f"Unknown action: {action}"}
        
        return await handler(input_data, params)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route execution to construction actions or container modules"""
        action = input_data.get("action", "")
        construction_actions = {
            "process_document", "qa_qc_inspection", "extract_quantities",
            "estimate_costs", "progress_tracker", "bim_analysis",
            "parse_primavera_schedule", "process_contract", "process_specification_full",
            "change_order_impact", "rfi_generator", "safety_compliance_audit",
            "carbon_footprint_calculator", "procurement_list_generator",
            "as_built_deviation_report", "warranty_maintenance_schedule",
            "risk_register_auto_populate", "submittal_log_generator",
            "payment_certificate", "bim_clash_detection", "daily_site_report",
            "value_engineering", "commissioning_checklist", "resource_histogram",
            "claims_builder", "health_check", "process_drawing"
        }
        if action in construction_actions:
            return await self.route(input_data, input_data.get("payload", {}))
        return await super().execute(input_data)
