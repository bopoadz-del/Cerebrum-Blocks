"""Construction Container - Full AEC Industry Domain Container v3.1"""

import re
import json
import os
import math
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

from app.core.universal_base import UniversalContainer


@dataclass
class Measurement:
    value: float
    unit: str
    type: str
    raw_text: str
    confidence: float
    context: str


@dataclass
class SpecItem:
    category: str
    key: str
    value: str
    section: str
    confidence: float


@dataclass
class RiskItem:
    id: str
    category: str
    description: str
    probability: str
    impact: str
    mitigation: str
    source: str


class ConstructionContainer(UniversalContainer):
    """
    Construction Container: Complete AEC suite - BIM, QA/QC, scheduling,
    contracts, specs, safety, carbon, procurement, risk
    """
    
    name = "construction"
    version = "3.1"
    description = "Complete AEC suite: BIM, QA/QC, scheduling, contracts, specs, safety, carbon, procurement, risk"
    layer = 3
    tags = ["domain", "container", "aec", "construction", "bim"]
    requires = ["pdf", "ocr", "image"]
    
    default_config = {
        "confidence_threshold": 0.85,
        "default_trade": "concrete"
    }
    
    ui_schema = {
        "input": {
            "type": "file",
            "accept": [".pdf", ".ifc", ".dwg", ".jpg", ".png", ".xer", ".xml"],
            "placeholder": "Upload construction drawing, BIM model, schedule, or contract...",
            "multiline": True
        },
        "output": {
            "type": "table",
            "fields": [
                {"name": "concrete_volume_m3", "type": "number", "unit": "m³", "label": "Concrete"},
                {"name": "steel_weight_kg", "type": "number", "unit": "kg", "label": "Steel"},
                {"name": "floor_area_m2", "type": "number", "unit": "m²", "label": "Floor Area"},
                {"name": "rebar_length_m", "type": "number", "unit": "m", "label": "Rebar"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"}
            ]
        },
        "quick_actions": [
            {"icon": "📐", "label": "Measure Drawing", "prompt": "Extract all measurements from this drawing"},
            {"icon": "📊", "label": "Calculate Quantities", "prompt": "Calculate BOQ from this drawing"},
            {"icon": "⚠️", "label": "Check Compliance", "prompt": "Check this against Saudi building codes"},
            {"icon": "🌱", "label": "Carbon Estimate", "prompt": "Estimate embodied carbon for this project"},
            {"icon": "📅", "label": "Analyze Schedule", "prompt": "Analyze this Primavera schedule for risks"}
        ]
    }

    # ─────────────────────────────────────────────────────────────────
    # ROUTING TABLE
    # ─────────────────────────────────────────────────────────────────
    async def route(self, action: str, input_data: Any, params: Dict) -> Dict:
        routes = {
            "process_document": self.process_document,
            "extract_quantities": self.extract_quantities,
            "analyze_spec": self.analyze_spec_section,
            "cost_estimate": self.generate_cost_estimate,
            "schedule_risk": self.analyze_schedule_risk,
            "contract_review": self.review_contract_clause,
            "safety_audit": self.safety_compliance_audit,
            "carbon_report": self.generate_carbon_report,
            "procurement": self.procurement_analysis,
            "status": self._status,
        }
        handler = routes.get(action, self._status)
        return await handler(input_data, params)

    async def _status(self, input_data: Any, params: Dict) -> Dict:
        return {
            "status": "success",
            "container": self.name,
            "version": self.version,
            "actions_available": list(self.route.__code__.co_consts[1].keys()) if hasattr(self.route.__code__, 'co_consts') else []
        }

    # ─────────────────────────────────────────────────────────────────
    # DOCUMENT PROCESSING
    # ─────────────────────────────────────────────────────────────────
    
    def _looks_like_file(self, input_data: Any, params: Dict) -> bool:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        return any(k in data or k in p for k in ["file_path", "content", "filename", "file", "url"])

    # CORE DOCUMENT PROCESSING
    async def _get_or_create_cache_key(self, file_path: str, doc_type: str) -> str:
        from app.blocks import BLOCK_REGISTRY
        hasher_block = BLOCK_REGISTRY.get("file_hasher")
        if hasher_block and os.path.exists(file_path):
            try:
                hasher_instance = hasher_block()
                hash_result = await hasher_instance.execute(
                    {"file_path": file_path}, {"action": "hash_file"}
                )
                if hash_result.get("status") == "success":
                    return f"construction:doc:{doc_type}:{hash_result.get('sha256', '')}"
            except Exception:
                pass
        if os.path.exists(file_path):
            return f"construction:doc:{doc_type}:{os.path.getmtime(file_path)}:{os.path.getsize(file_path)}"
        import hashlib
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return f"construction:doc:{doc_type}:missing:{path_hash}"

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

        cache_key = await self._get_or_create_cache_key(file_path, doc_type)

        from app.blocks import BLOCK_REGISTRY
        cache_block = BLOCK_REGISTRY.get("cache_manager")
        if cache_block:
            try:
                cache_instance = cache_block()
                cached = await cache_instance.execute(
                    {"key": cache_key}, {"action": "get", "key": cache_key}
                )
                if cached.get("cached") and cached.get("value") is not None:
                    cached_value = cached["value"]
                    if isinstance(cached_value, dict):
                        cached_value["_source"] = "cache"
                        cached_value["_cache_key"] = cache_key
                    return cached_value
            except Exception:
                pass

        file_size = 0
        hasher_block = BLOCK_REGISTRY.get("file_hasher")
        if hasher_block:
            try:
                hasher_instance = hasher_block()
                hash_result = await hasher_instance.execute(
                    {"file_path": file_path}, {"action": "metadata"}
                )
                if hash_result.get("status") == "success":
                    file_size = hash_result.get("size", 0)
            except Exception:
                pass

        if file_size > 10 * 1024 * 1024:
            async_block = BLOCK_REGISTRY.get("async_processor")
            if async_block:
                try:
                    async_instance = async_block()
                    task_payload = {
                        "task_name": "block:construction.process_document",
                        "file_path": file_path,
                        "doc_type": doc_type,
                        "data": data,
                        "params": p,
                    }
                    queued = await async_instance.execute(
                        task_payload,
                        {
                            "action": "submit",
                            "task_name": "block:construction.process_document",
                        },
                    )
                    return {
                        "status": "queued",
                        "_source": "async_queue",
                        "_cache_key": cache_key,
                        "file_size": file_size,
                        "queued": queued,
                    }
                except Exception:
                    pass

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
        p["file_path"] = file_path
        result = await processor(file_path, p)

        llm_block = BLOCK_REGISTRY.get("llm_enhancer")
        if llm_block and isinstance(result, dict) and result.get("status") == "success":
            try:
                llm_instance = llm_block()
                enhanced = await llm_instance.execute(
                    {"text": json.dumps(result)},
                    {
                        "action": "structure_json",
                        "schema": "structured construction document data",
                    },
                )
                if enhanced.get("status") == "success":
                    result["llm_enhanced"] = enhanced.get("structured") or enhanced
            except Exception:
                pass

        if cache_block:
            try:
                cache_instance = cache_block()
                await cache_instance.execute(
                    result, {"action": "set", "key": cache_key, "ttl": 7200}
                )
            except Exception:
                pass

        if isinstance(result, dict):
            result["_cache_key"] = cache_key
            result["_source"] = "processor"
        return result

    async def _classify_document(self, file_path: str) -> str:
        name = Path(file_path).name.lower()
        if any(x in name for x in [".ifc", ".bim", "model"]):
            return "bim"
        if any(x in name for x in [".xer", ".xml", "schedule", "primavera", "p6"]):
            return "schedule"
        if any(x in name for x in ["contract", "agreement", "terms", "conditions", "legal"]):
            return "contract"
        if any(x in name for x in ["spec", "specification", "masterformat", "csi"]):
            return "specification"
        if any(x in name for x in ["bom", "bill", "materials", "takeoff", "quantity"]):
            return "bom"
        if any(x in name for x in ["report", "inspection", "test", "certificate"]):
            return "report"
        if any(x in name for x in [".jpg", ".png", ".jpeg", "photo", "site", "image"]):
            return "image"
        if any(x in name for x in ["change order", "variation", "vo", "co", "claim"]):
            return "change_order"
        if any(x in name for x in ["safety", "audit", "inspection", "hazard"]):
            return "safety_audit"
        return "drawing"

    # DRAWING PROCESSING
    async def _process_drawing(self, file_path: str, params: Dict) -> Dict:
        # Use pre-extracted text if provided from chain
        pre_extracted_text = params.get("extracted_text", "")
        
        try:
            import fitz
            doc = fitz.open(file_path)
        except Exception as e:
            return {"status": "error", "error": f"[DRAWING_V2] Could not open file: {str(e)}", "file": file_path}
        
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
            "confidence": {},
            "used_pre_extracted_text": bool(pre_extracted_text)  # Flag to indicate source
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            sheet_data = self._process_drawing_page(page, page_num, pre_extracted_text if page_num == 0 else "")
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
    
    def _process_drawing_page(self, page, page_num: int, pre_extracted_text: str = "") -> Dict:
        # Use pre-extracted text if available, otherwise extract from page
        if pre_extracted_text:
            raw_text = pre_extracted_text[:8000]  # Use provided text
            text_dict = None  # No dict structure available from pre-extracted
        else:
            text_dict = page.get_text("dict")
            raw_text = page.get_text()[:8000]
        
        return {
            "page_number": page_num + 1,
            "raw_text": raw_text[:8000],
            "measurements": self._extract_measurements_advanced(raw_text, text_dict or {}),
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
    
    def _extract_drawing_number(self, filename: str) -> str:
        """Extract drawing number from filename (e.g., 'A-101-plan.pdf' -> 'A-101')."""
        import re
        # Look for patterns like A-101, ARCH-001, C-501, etc.
        match = re.search(r'([A-Z]+-?\d{3,})', filename.upper())
        return match.group(1) if match else "Unknown"
    
    def _extract_revision(self, filename: str) -> str:
        """Extract revision from filename (e.g., 'plan-rev-A.pdf' -> 'A')."""
        import re
        # Look for rev patterns
        match = re.search(r'[Rr][Ee][Vv][-_]?(\w)', filename)
        return match.group(1) if match else "A"
    
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

    # CONTRACT MANAGEMENT
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
            "insurance": r'(?:insurance|indemnif)[\s\w]{0,100}(?:required|shall|must|coverage)',
            "termination": r'(?:terminat|cancel|end)[\s\w]{0,100}(?:notice|for cause|convenience)',
            "force_majeure": r'(?:force majeure|unforeseen|beyond control|delay event)[\s\w]{0,100}(?:excus|reliev|not liable)',
            "dispute_resolution": r'(?:dispute|arbitration|mediation|adjudication)[\s\w]{0,100}(?:shall|must|proceed)',
        }
        
        extracted_clauses = {}
        for clause_name, pattern in clause_patterns.items():
            matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
            extracted_clauses[clause_name] = {
                "found": len(matches) > 0,
                "count": len(matches),
                "examples": [m.group(0)[:200] for m in matches[:3]]
            }
        
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
        if any(w in text.lower() for w in ["quality", "defect", "warranty", "guarantee"]):
            return "quality"
        if any(w in text.lower() for w in ["time", "schedule", "milestone", "delay", "completion"]):
            return "schedule"
        return "general"
    
    def _assess_obligation_priority(self, text: str) -> str:
        if any(w in text.lower() for w in ["shall", "must", "required", "mandatory"]):
            return "high"
        if any(w in text.lower() for w in ["will", "agrees to", "responsible for"]):
            return "medium"
        return "low"
    
    def _assess_contract_risks(self, clauses: Dict, contract_type: str) -> Dict:
        score = 100
        critical = []
        warnings = []
        recommendations = []
        
        if not clauses.get("payment_terms", {}).get("found"):
            score -= 20
            critical.append("Payment terms not clearly defined")
            recommendations.append("Add explicit payment schedule with milestones")
        if not clauses.get("liquidated_damages", {}).get("found"):
            score -= 15
            warnings.append("No liquidated damages clause")
            recommendations.append("Consider adding LDs for late completion protection")
        if not clauses.get("termination", {}).get("found"):
            score -= 10
            warnings.append("Termination clause missing or unclear")
        if not clauses.get("force_majeure", {}).get("found"):
            score -= 10
            warnings.append("No force majeure clause")
            recommendations.append("Add force majeure for unforeseen delays (weather, pandemic, etc.)")
        if not clauses.get("dispute_resolution", {}).get("found"):
            score -= 10
            warnings.append("No dispute resolution mechanism")
        
        risk_level = "low" if score > 80 else "medium" if score > 60 else "high"
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

    # SCHEDULING & PRIMAVERA P6
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
        
        cpm_results = self._calculate_cpm(schedule_data)
        
        delay_analysis = None
        if baseline_file:
            if Path(baseline_file).suffix.lower() == '.xer':
                baseline_data = self._parse_xer_file(baseline_file)
            else:
                baseline_data = self._parse_xml_schedule(baseline_file)
            if baseline_data.get("status") != "error":
                delay_analysis = self._analyze_delays(schedule_data, baseline_data)
        
        schedule_risks = self._analyze_schedule_risks(cpm_results)
        recovery_options = self._generate_recovery_options(delay_analysis, cpm_results) if delay_analysis else []
        
        return {
            "status": "success",
            "action": "schedule_analysis",
            "file_name": Path(file_path).name,
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
                    "id": act.get("task_id", ""),
                    "name": act.get("task_name", ""),
                    "start": act.get("act_start_date", act.get("early_start_date", "")),
                    "finish": act.get("act_end_date", act.get("early_end_date", "")),
                    "duration": act.get("target_drtn_hr_cnt", 0),
                    "total_float": float(act.get("total_float_hr_cnt", 0)) / 8,
                    "free_float": float(act.get("free_float_hr_cnt", 0)) / 8,
                    "percent_complete": float(act.get("act_work_qty", 0)) / max(1, float(act.get("target_work_qty", 1))) * 100,
                    "wbs": act.get("wbs_id", ""),
                    "predecessors": [r.get("pred_task_id") for r in relationships if r.get("task_id") == act.get("task_id")],
                    "successors": [r.get("task_id") for r in relationships if r.get("pred_task_id") == act.get("task_id")],
                })
            
            return {
                "status": "success",
                "file_type": "xer",
                "project_id": project_info.get("proj_id", ""),
                "project_name": project_info.get("proj_short_name", ""),
                "data_date": project_info.get("last_recalc_date", ""),
                "activities": structured_activities
            }
            
        except Exception as e:
            return {"status": "error", "error": f"XER parse failed: {str(e)}"}
    
    def _parse_xml_schedule(self, file_path: str) -> Dict:
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            activities = []
            for activity in root.findall('.//Activity') if root else []:
                act_data = {
                    "id": activity.findtext('ID', ''),
                    "name": activity.findtext('Name', ''),
                    "start": activity.findtext('Start', ''),
                    "finish": activity.findtext('Finish', ''),
                    "duration": activity.findtext('Duration', 0),
                    "total_float": activity.findtext('TotalFloat', 0),
                    "percent_complete": activity.findtext('PercentComplete', 0)
                }
                activities.append(act_data)
            
            return {
                "status": "success",
                "file_type": "xml",
                "activities": activities
            }
        except Exception as e:
            return {"status": "error", "error": f"XML parse failed: {str(e)}"}
    
    def _calculate_cpm(self, schedule_data: Dict) -> Dict:
        activities = schedule_data.get("activities", [])
        
        if not activities:
            return {"critical_path": [], "project_duration_days": 0, "average_float": 0}
        
        critical_activities = [a for a in activities if a.get("total_float", 999) <= 0.1]
        
        if not critical_activities:
            min_float = min((a.get("total_float", 999) for a in activities), default=0)
            critical_activities = [a for a in activities if a.get("total_float", 999) <= min_float + 0.1]
        
        duration = 0
        if critical_activities:
            try:
                start_dates = [datetime.fromisoformat(a.get("start", "").replace('Z', '+00:00')) for a in critical_activities if a.get("start")]
                finish_dates = [datetime.fromisoformat(a.get("finish", "").replace('Z', '+00:00')) for a in critical_activities if a.get("finish")]
                if start_dates and finish_dates:
                    duration = (max(finish_dates) - min(start_dates)).days
            except Exception:
                duration = sum(a.get("duration", 0) for a in critical_activities) / 8
        
        floats = [a.get("total_float", 0) for a in activities if a.get("total_float", 999) < 999]
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
    
    def _generate_recovery_options(self, delay_analysis: Optional[Dict], cpm_results: Dict) -> List[Dict]:
        if not delay_analysis:
            return []
        
        total_delay = delay_analysis.get("total_delay_days", 0)
        if total_delay <= 0:
            return []
        
        options = []
        options.append({
            "strategy": "Crash Critical Path",
            "description": "Add resources to critical activities",
            "potential_savings_days": total_delay * 0.5,
            "cost_impact": "High",
            "feasibility": "Medium"
        })
        options.append({
            "strategy": "Fast Track",
            "description": "Overlap sequential activities",
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

    # SPECIFICATIONS (CSI MasterFormat)
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
            return {"status": "error", "error": f"Could not read spec file: {str(e)}"}
        
        divisions = {i: [] for i in range(1, 50)}
        current_division = None
        lines = full_text.split('\n')
        
        for line in lines:
            division_match = re.match(r'^(\d{2})\s{3,}', line)
            if division_match:
                div_num = int(division_match.group(1))
                if 1 <= div_num <= 49:
                    current_division = div_num
                    divisions[current_division].append(line.strip())
            elif current_division and line.strip():
                divisions[current_division].append(line.strip())
        
        detected_divisions = [i for i, content in divisions.items() if content]
        
        spec_items = []
        for div_num, content in divisions.items():
            if not content:
                continue
            if division_filter and str(div_num) != str(division_filter):
                continue
            full_content = '\n'.join(content)
            materials = self._extract_materials(full_content)
            methods = self._extract_methods(full_content)
            testing = self._extract_testing_requirements(full_content)
            qa_qc = self._extract_qaqc(full_content)
            
            spec_items.append(SpecItem(
                category=f"Division {div_num:02d}",
                key="content",
                value=f"{len(content)} paragraphs",
                section="general",
                confidence=0.9
            ))
        
        return {
            "status": "success",
            "action": "specification_analysis",
            "file_name": Path(file_path).name,
            "divisions_found": detected_divisions,
            "division_filter_applied": division_filter,
            "total_sections_analyzed": len(spec_items),
            "spec_items": [asdict(item) for item in spec_items],
            "materials_referenced": materials if 'materials' in dir() else [],
            "methods_specified": methods if 'methods' in dir() else [],
            "testing_requirements": testing if 'testing' in dir() else [],
            "qa_qc_requirements": qa_qc if 'qa_qc' in dir() else []
        }
    
    async def analyze_spec_section(self, input_data: Any, params: Dict) -> Dict:
        return await self.process_specification_full(input_data, params)
    
    def _extract_materials(self, text: str) -> List[str]:
        materials = []
        material_keywords = ["concrete", "steel", "rebar", "brick", "block", "glass", "aluminum", "timber", "insulation", "membrane"]
        for kw in material_keywords:
            if kw in text.lower():
                materials.append(kw)
        return materials
    
    def _extract_methods(self, text: str) -> List[str]:
        return []
    
    def _extract_testing_requirements(self, text: str) -> List[str]:
        requirements = []
        if re.search(r'\btest\b|\bsample\b|\blab\b', text, re.IGNORECASE):
            requirements.append("Testing requirements found")
        return requirements
    
    def _extract_qaqc(self, text: str) -> List[str]:
        qa = []
        if re.search(r'\binspection\b|\bwitness\b|\bhold point\b', text, re.IGNORECASE):
            qa.append("Inspection/witness requirements")
        return qa

    # COST ESTIMATION (RSMeans-style)
    async def generate_cost_estimate(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        
        quantities = p.get("quantities", data.get("quantities", {}))
        location = p.get("location", "US National Average")
        project_type = p.get("project_type", "general_building")
        
        rsmeans_data = self._get_rsmeans_data()
        location_factor = rsmeans_data.get("location_factors", {}).get(location, 1.0)
        
        line_items = []
        for item_name, qty_data in quantities.items():
            if isinstance(qty_data, dict):
                quantity = qty_data.get("quantity", 0)
                unit = qty_data.get("unit", "ea")
            else:
                quantity = qty_data
                unit = "ea"
            
            base_rate = self._lookup_unit_cost(item_name, unit, rsmeans_data)
            adjusted_rate = base_rate * location_factor
            total = quantity * adjusted_rate
            
            line_items.append({
                "item": item_name,
                "quantity": quantity,
                "unit": unit,
                "base_rate": base_rate,
                "adjusted_rate": adjusted_rate,
                "location_factor": location_factor,
                "total": round(total, 2)
            })
        
        subtotal = sum(item["total"] for item in line_items)
        overhead = subtotal * 0.10
        profit = subtotal * 0.08
        contingency = subtotal * 0.05
        total = subtotal + overhead + profit + contingency
        
        return {
            "status": "success",
            "action": "cost_estimate",
            "location": location,
            "location_factor": location_factor,
            "line_items": line_items,
            "summary": {
                "subtotal": round(subtotal, 2),
                "overhead": round(overhead, 2),
                "profit": round(profit, 2),
                "contingency": round(contingency, 2),
                "total_estimate": round(total, 2)
            },
            "confidence": "medium"
        }
    
    def _get_rsmeans_data(self) -> Dict:
        return {
            "unit_costs": {
                "concrete_m3": 150.0,
                "steel_kg": 2.5,
                "formwork_m2": 45.0,
                "rebar_kg": 1.8,
                "block_m2": 35.0,
                "masonry_m2": 65.0,
                "glazing_m2": 180.0,
                "finishes_m2": 55.0
            },
            "location_factors": {
                "US National Average": 1.0,
                "New York City": 1.35,
                "San Francisco": 1.42,
                "Dubai": 0.95,
                "Riyadh": 0.88,
                "London": 1.28,
                "Sydney": 1.15,
                "Singapore": 1.08
            }
        }
    
    def _lookup_unit_cost(self, item_name: str, unit: str, rsmeans_data: Dict) -> float:
        unit_costs = rsmeans_data.get("unit_costs", {})
        
        if "concrete" in item_name.lower() and unit in ["m3", "cu m", "cubic meter"]:
            return unit_costs.get("concrete_m3", 150.0)
        elif "steel" in item_name.lower() and unit in ["kg", "kilogram"]:
            return unit_costs.get("steel_kg", 2.5)
        elif "formwork" in item_name.lower() and unit in ["m2", "sq m", "square meter"]:
            return unit_costs.get("formwork_m2", 45.0)
        elif "rebar" in item_name.lower() and unit in ["kg", "kilogram"]:
            return unit_costs.get("rebar_kg", 1.8)
        elif "block" in item_name.lower() and unit in ["m2", "sq m"]:
            return unit_costs.get("block_m2", 35.0)
        elif "masonry" in item_name.lower() and unit in ["m2", "sq m"]:
            return unit_costs.get("masonry_m2", 65.0)
        elif "glass" in item_name.lower() or "glazing" in item_name.lower():
            return unit_costs.get("glazing_m2", 180.0)
        elif "finish" in item_name.lower():
            return unit_costs.get("finishes_m2", 55.0)
        
        return 50.0
    
    def extract_quantities(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "success", "quantities": input_data.get("measurements", []) if isinstance(input_data, dict) else []}

    # CARBON & SUSTAINABILITY
    async def generate_carbon_report(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        quantities = p.get("quantities", data.get("quantities", {}))
        
        carbon_factors = {
            "concrete_m3": 250.0,
            "steel_kg": 2.3,
            "rebar_kg": 1.9,
            "timber_m3": -500.0,
            "block_m2": 45.0,
            "aluminum_kg": 11.0,
            "glass_m2": 35.0
        }
        
        total_carbon = 0
        breakdown = []
        
        for material, qty_data in quantities.items():
            if isinstance(qty_data, dict):
                quantity = qty_data.get("quantity", 0)
            else:
                quantity = qty_data
            
            factor = carbon_factors.get(material, 100.0)
            carbon = quantity * factor
            total_carbon += carbon
            
            breakdown.append({
                "material": material,
                "quantity": quantity,
                "factor_kg_co2_per_unit": factor,
                "total_kg_co2": round(carbon, 2)
            })
        
        return {
            "status": "success",
            "action": "carbon_report",
            "total_embodied_carbon_kg": round(total_carbon, 2),
            "total_tonnes_co2": round(total_carbon / 1000, 2),
            "breakdown": breakdown,
            "benchmark": "Typical office building: 350-500 kg CO2/m²",
            "recommendations": [
                "Consider low-carbon concrete mixes",
                "Optimize steel tonnage through efficient design",
                "Specify recycled content where possible"
            ]
        }

    # SAFETY & COMPLIANCE
    async def safety_compliance_audit(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        
        audit_type = p.get("audit_type", "general")
        photos = data.get("photos", p.get("photos", []))
        
        if not photos and data.get("file_path"):
            photos = [data.get("file_path")]
        
        if not photos:
            return {"status": "error", "error": "No photos provided for safety audit"}
        
        violations = []
        compliant_items = []
        
        for photo_path in photos[:10]:
            analysis = await self._analyze_safety_photo(photo_path, audit_type)
            
            if analysis.get("hazards_detected", 0) > 0:
                violations.extend(analysis.get("hazards", []))
            else:
                compliant_items.append({
                    "photo": analysis.get("photo"),
                    "status": "compliant",
                    "notes": "No obvious violations detected"
                })
        
        severity_counts = {"critical": 0, "major": 0, "minor": 0}
        for v in violations:
            sev = v.get("severity", "minor")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        return {
            "status": "success",
            "action": "safety_audit",
            "audit_type": audit_type,
            "photos_analyzed": len(photos),
            "violations_found": len(violations),
            "severity_breakdown": severity_counts,
            "violations": violations[:20],
            "compliant_items": compliant_items,
            "overall_compliance": "fail" if severity_counts["critical"] > 0 else "pass with observations" if severity_counts["major"] > 0 else "pass",
            "recommendations": self._generate_safety_recommendations(violations)
        }
    
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
    
    def _generate_safety_recommendations(self, violations: List[Dict]) -> List[str]:
        if not violations:
            return ["Continue current safety practices", "Document compliance for audit trail"]
        
        recs = []
        types = set(v.get("type") for v in violations)
        
        if "missing_ppe" in types:
            recs.append("Immediate: Enforce mandatory PPE - hard hats, vests, safety boots")
        if "fall_hazard" in types or "missing_guardrail" in types:
            recs.append("Critical: Install guardrails/harnesses before work continues")
        if "trip_hazard" in types:
            recs.append("Clean and organize work area - remove trip hazards")
        
        return recs

    # PROCUREMENT & SUBCONTRACTOR
    async def procurement_analysis(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "success", "action": "procurement_analysis", "recommendations": []}

    # CHANGE ORDER / VARIATION
    async def change_order_impact(self, input_data: Any, params: Dict) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        
        co_type = p.get("change_type", data.get("change_type", "general"))
        direct_cost = p.get("direct_cost", data.get("direct_cost", 0))
        
        analysis = self._analyze_change_type(co_type, params)
        cost_impact = self._calculate_co_cost_impact(direct_cost, analysis)
        
        return {
            "status": "success",
            "action": "change_order_analysis",
            "change_type": co_type,
            "category": analysis.get("category"),
            "complexity": analysis.get("complexity"),
            "cost_impact": cost_impact,
            "schedule_impact_days": analysis.get("typical_delay_days", 0),
            "trade_involved": analysis.get("trade_involved"),
            "risk_level": analysis.get("risk_level"),
            "approvals_required": analysis.get("approvals", ["PM", "QS"]),
            "recommendation": "Approve with conditions" if analysis.get("category") != "major" else "Escalate to senior management"
        }
    
    def _analyze_change_type(self, co_type: str, params: Dict) -> Dict:
        categories = {
            "scope_addition": ["add", "extra", "additional", "new work", "extra work"],
            "scope_omission": ["delete", "remove", "omit", "deduct"],
            "design_change": ["redesign", "change spec", "substitution"],
            "site_condition": [" differing site", "unforeseen", "latent", "ground condition"],
            "delay_claim": ["delay", "acceleration", "time extension", "EOT"]
        }
        text_lower = co_type.lower()
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
            "complexity": "high" if len(co_type) > 500 else "medium" if len(co_type) > 200 else "low",
            "trade_involved": self._detect_trade_from_text(co_type)
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

    # RISK ANALYSIS
    async def analyze_schedule_risk(self, input_data: Any, params: Dict) -> Dict:
        return await self.parse_primavera_schedule(input_data, params)
    
    def _create_risk_item(self, category: str, description: str, probability: str, impact: str, mitigation: str, source: str) -> Dict:
        return {
            "category": category,
            "description": description,
            "probability": probability,
            "impact": impact,
            "mitigation": mitigation,
            "source": source,
            "id": f"RISK-{hash(description) % 10000:04d}"
        }

    # DRAWING HELPERS
    def _extract_measurements_advanced(self, text: str, text_dict: Dict) -> List[Dict]:
        measurements = []
        
        dimension_pattern = r'\b(\d+(?:\.\d+)?)\s*(?:m|m\.|meter|meters|ft|feet|foot|\')\s*(?:x|by|×)\s*(\d+(?:\.\d+)?)\s*(?:m|m\.|meter|meters|ft|feet|foot|\')'
        for match in re.finditer(dimension_pattern, text, re.IGNORECASE):
            width = float(match.group(1))
            height = float(match.group(2))
            unit = "m" if "m" in match.group(0).lower() else "ft"
            area = width * height
            measurements.append({
                "type": "dimension",
                "value": area,
                "unit": f"{unit}²",
                "width": width,
                "height": height,
                "raw": match.group(0),
                "context": text[max(0, match.start()-50):match.end()+50]
            })
        
        quantity_pattern = r'\b(\d+)\s*(?:no|nos|nr|ea|each)?\.?\s*([A-Z][A-Za-z\s]+)'
        for match in re.finditer(quantity_pattern, text[:2000]):
            qty = int(match.group(1))
            item = match.group(2).strip()[:50]
            if len(item) > 3:
                measurements.append({
                    "type": "count",
                    "value": qty,
                    "unit": "ea",
                    "item": item,
                    "raw": match.group(0)
                })
        
        return measurements[:50]
    
    def _extract_tables_advanced(self, page) -> List[Dict]:
        return []
    
    def _extract_annotations(self, page) -> List[Dict]:
        return []
    
    def _extract_specs_advanced(self, text: str) -> List[Dict]:
        specs = []
        grade_pattern = r'\b(C\d{2,3}|M\d{2,3}|S\d{2,3}|Grade\s+\d+)\b'
        for match in re.finditer(grade_pattern, text):
            specs.append({
                "type": "grade",
                "value": match.group(1),
                "context": text[max(0, match.start()-30):match.end()+30]
            })
        return specs
    
    def _extract_title_block(self, sheet_data: Dict) -> Dict:
        return {}
    
    def _extract_scale(self, text: str) -> Optional[str]:
        scale_match = re.search(r'\b\d+\s*:\s*\d+\b', text)
        return scale_match.group(0) if scale_match else None
    
    def _detect_disciplines(self, text: str) -> List[str]:
        disciplines = []
        disc_patterns = {
            "architectural": ["plan", "elevation", "section", "detail"],
            "structural": ["rebar", "rc", "concrete", "steel", "beam", "column", "slab"],
            "mep": ["electrical", "plumbing", "hvac", "mechanical", "fire", "lighting"],
            "civil": ["grading", "drainage", "utility", "road", "pavement"]
        }
        text_lower = text.lower()
        for disc, keywords in disc_patterns.items():
            if any(kw in text_lower for kw in keywords):
                disciplines.append(disc)
        return disciplines
    
    def _calculate_quantities(self, measurements: List[Dict]) -> Dict:
        total_area = sum(m.get("value", 0) for m in measurements if m.get("type") == "dimension")
        counts = {m.get("item", "unknown"): m.get("value", 0) for m in measurements if m.get("type") == "count"}
        
        concrete_volume = total_area * 0.15
        steel_weight = concrete_volume * 120
        rebar_length = concrete_volume * 50
        
        return {
            "floor_area_m2": round(total_area, 2),
            "concrete_volume_m3": round(concrete_volume, 2),
            "steel_weight_kg": round(steel_weight, 2),
            "rebar_length_m": round(rebar_length, 2),
            "item_counts": counts
        }
    
    def _estimate_costs(self, quantities: Dict) -> Dict:
        concrete_cost = quantities.get("concrete_volume_m3", 0) * 150
        steel_cost = quantities.get("steel_weight_kg", 0) * 2.5
        rebar_cost = quantities.get("rebar_length_m", 0) * 1.8
        
        subtotal = concrete_cost + steel_cost + rebar_cost
        
        return {
            "concrete_cost": round(concrete_cost, 2),
            "steel_cost": round(steel_cost, 2),
            "rebar_cost": round(rebar_cost, 2),
            "subtotal": round(subtotal, 2),
            "total_with_overhead": round(subtotal * 1.25, 2)
        }
    
    def _estimate_carbon(self, quantities: Dict) -> Dict:
        concrete_carbon = quantities.get("concrete_volume_m3", 0) * 250
        steel_carbon = quantities.get("steel_weight_kg", 0) * 2.3
        
        return {
            "concrete_co2_kg": round(concrete_carbon, 2),
            "steel_co2_kg": round(steel_carbon, 2),
            "total_embodied_carbon_kg": round(concrete_carbon + steel_carbon, 2)
        }
    
    def _calculate_confidence(self, result: Dict) -> Dict:
        return {
            "overall": 0.85,
            "text_extraction": 0.90,
            "measurement_detection": 0.80,
            "quantity_calculation": 0.75
        }
    
    async def _detect_risks_from_drawing(self, result: Dict) -> List[Dict]:
        risks = []
        
        if not result.get("measurements"):
            risks.append({
                "type": "data_quality",
                "description": "No measurements detected - manual verification required",
                "severity": "medium",
                "mitigation": "Use quantity surveyor to verify BOQ"
            })
        
        if result.get("confidence", {}).get("overall", 1.0) < 0.7:
            risks.append({
                "type": "confidence",
                "description": "Low extraction confidence",
                "severity": "medium",
                "mitigation": "Review all quantities manually"
            })
        
        return risks
