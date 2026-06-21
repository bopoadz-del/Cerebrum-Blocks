"""Education Block v2 - TypedBlock implementation

This is the v2 implementation that:
- Extends TypedBlock instead of UniversalContainer
- Accepts TextContent input (from pdf_v2, ocr_v2, etc.)
- Outputs EducationAnalysis type
- Has a single process() entry point instead of action routing
- Internal methods are private (_ prefixed)
- Uses deterministic regex + math, no LLM calls, no external APIs
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.typed_block import TypedBlock
from app.core.schema_registry import TextContent, EducationAnalysis
from app.core.confidence import assess_extraction_confidence
from app.core.education_types import EducationEntity, EducationMetric, ComplianceFlag, RiskScore
from app.core.education_knowledge import EducationKnowledge, COMPLIANCE_KEYWORDS

_rk = EducationKnowledge()


class EducationBlockV2(TypedBlock):
    """
    Education Block v2 - TypedBlock implementation for education document analysis.

    Input: TextContent (extracted document text)
    Output: EducationAnalysis (entities, metrics, compliance flags, risk scores)
    """

    name = "education_v2"
    version = "2.0"
    description = "Education document analysis with typed input/output"
    layer = 3
    tags = ["domain", "education", "v2"]
    requires = []

    default_config = {
        "confidence_threshold": 0.85,
    }

    input_schema = TextContent
    output_schema = EducationAnalysis

    accepted_input_types = ["TextContent", "PDFContent"]
    produced_output_types = ["EducationAnalysis"]

    ui_schema = {
        "input": {
            "type": "text",
            "placeholder": "Paste education document text...",
            "multiline": True,
        },
        "output": {
            "type": "table",
            "fields": [
                {"name": "gpa", "type": "number", "label": "GPA"},
                {"name": "completion_rate", "type": "number", "label": "Completion Rate %"},
                {"name": "retention_rate", "type": "number", "label": "Retention Rate %"},
                {"name": "graduation_rate", "type": "number", "label": "Graduation Rate %"},
                {"name": "academic_risk", "type": "number", "label": "Academic Risk"},
                {"name": "compliance_risk", "type": "number", "label": "Compliance Risk"},
                {"name": "financial_risk", "type": "number", "label": "Financial Risk"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"},
            ],
        },
        "quick_actions": [
            {"icon": "📄", "label": "Analyze Transcript", "prompt": "Analyze this transcript"},
            {"icon": "🎓", "label": "Check FERPA Compliance", "prompt": "Check this document for FERPA compliance"},
            {"icon": "⚠️", "label": "Score Education Risks", "prompt": "Score education risks for this document"},
            {"icon": "🔍", "label": "Extract Courses & Grades", "prompt": "Extract courses and grades from this document"},
        ],
    }

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Main entry point - analyze education document text."""
        params = params or {}

        text = self._extract_text(input_data)
        if not text:
            return self._empty_analysis("No text provided")

        custom_rules = params.get("custom_rules") or params.get("rules")
        if custom_rules:
            _rk.set_custom_rules(custom_rules)

        document_type = params.get("document_type") or params.get("analysis_type") or self._detect_document_type(text)

        if document_type == "student_record":
            return await self._analyze_student_record(text, params)
        if document_type == "individual_education_plan":
            return await self._analyze_individual_education_plan(text, params)
        if document_type == "accreditation_report":
            return await self._analyze_accreditation_report(text, params)
        if document_type == "syllabus":
            return await self._analyze_syllabus(text, params)
        if document_type == "financial_aid":
            return await self._analyze_financial_aid(text, params)
        if document_type == "disciplinary_record":
            return await self._analyze_disciplinary_record(text, params)
        if document_type == "faculty_contract":
            return await self._analyze_faculty_contract(text, params)
        if document_type == "admissions_file":
            return await self._analyze_admissions_file(text, params)

        return await self._analyze_generic(text, params)

    # ------------------------------------------------------------------
    # TEXT EXTRACTION
    # ------------------------------------------------------------------

    def _extract_text(self, input_data: Any) -> str:
        """Extract text from TextContent or plain string."""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            if "text" in input_data:
                return input_data["text"]
            return input_data.get("content", "")
        return ""

    def _empty_analysis(self, message: str) -> Dict[str, Any]:
        """Return a minimal failed/empty analysis."""
        return {
            "status": "error",
            "error": message,
            "document_type": "unknown",
            "entities": {},
            "metrics": {},
            "financials": {},
            "compliance_flags": {},
            "risk_scores": {},
            "confidence": 0.0,
            "metadata": {"extracted_at": self._timestamp()},
        }

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # DOCUMENT TYPE DETECTION
    # ------------------------------------------------------------------

    def _detect_document_type(self, text: str) -> str:
        """Auto-detect education document type from content."""
        text_lower = text[:5000].lower()

        if any(kw in text_lower for kw in ['transcript', 'gpa', 'credits', 'enrollment', 'major', 'minor', 'degree', 'graduation']):
            return "student_record"
        if any(kw in text_lower for kw in ['iep', 'special education', 'accommodation', 'disability', 'goals', 'services']):
            return "individual_education_plan"
        if any(kw in text_lower for kw in ['accreditation', 'self-study', 'standards', 'criteria', 'peer review', 'site visit']):
            return "accreditation_report"
        if any(kw in text_lower for kw in ['syllabus', 'course outline', 'learning objectives', 'assignments', 'grading rubric', 'textbook']):
            return "syllabus"
        if any(kw in text_lower for kw in ['fafsa', 'scholarship', 'grant', 'loan', 'pell', 'work-study', 'efc', 'award letter']):
            return "financial_aid"
        if any(kw in text_lower for kw in ['disciplinary', 'violation', 'suspension', 'expulsion', 'code of conduct', 'hearing']):
            return "disciplinary_record"
        if any(kw in text_lower for kw in ['tenure', 'appointment', 'sabbatical', 'course load', 'research', 'publication', 'ip']):
            return "faculty_contract"
        if any(kw in text_lower for kw in ['application', 'sat', 'act', 'gpa', 'recommendation', 'essay', 'waitlist', 'deferred']):
            return "admissions_file"

        return "generic"

    # ------------------------------------------------------------------
    # ANALYSIS METHODS (private)
    # ------------------------------------------------------------------

    async def _analyze_student_record(self, text: str, params: Dict) -> Dict:
        """Analyze student record text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "student_record"
        return self._finalize_result(result, params)

    async def _analyze_individual_education_plan(self, text: str, params: Dict) -> Dict:
        """Analyze individual education plan text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "individual_education_plan"
        return self._finalize_result(result, params)

    async def _analyze_accreditation_report(self, text: str, params: Dict) -> Dict:
        """Analyze accreditation report text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "accreditation_report"
        return self._finalize_result(result, params)

    async def _analyze_syllabus(self, text: str, params: Dict) -> Dict:
        """Analyze syllabus text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "syllabus"
        return self._finalize_result(result, params)

    async def _analyze_financial_aid(self, text: str, params: Dict) -> Dict:
        """Analyze financial aid text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "financial_aid"
        return self._finalize_result(result, params)

    async def _analyze_disciplinary_record(self, text: str, params: Dict) -> Dict:
        """Analyze disciplinary record text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "disciplinary_record"
        return self._finalize_result(result, params)

    async def _analyze_faculty_contract(self, text: str, params: Dict) -> Dict:
        """Analyze faculty contract text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "faculty_contract"
        return self._finalize_result(result, params)

    async def _analyze_admissions_file(self, text: str, params: Dict) -> Dict:
        """Analyze admissions file text."""
        result = self._build_analysis(text, params)
        result["document_type"] = "admissions_file"
        return self._finalize_result(result, params)

    async def _analyze_generic(self, text: str, params: Dict) -> Dict:
        """Generic analysis for unknown document types."""
        result = self._build_analysis(text, params)
        result["document_type"] = "generic"
        return self._finalize_result(result, params)

    # ------------------------------------------------------------------
    # BUILDERS
    # ------------------------------------------------------------------

    def _build_analysis(self, text: str, params: Dict) -> Dict:
        """Run all extraction passes and return a working dict."""
        entities = {
            "student_ids": self._extract_student_ids(text),
            "course_codes": self._extract_course_codes(text),
            "credit_hours": self._extract_credit_hours(text),
            "grades": self._extract_grades(text),
            "instructors": self._extract_instructors(text),
            "institutions": self._extract_institutions(text),
            "programs": self._extract_programs(text),
            "semesters": self._extract_semesters(text),
        }
        metrics = {
            "gpa": self._extract_gpa(**params.get("gpa", {})),
            "completion_rate": self._extract_completion_rate(**params.get("completion_rate", {})),
            "retention_rate": self._extract_retention_rate(**params.get("retention_rate", {})),
            "graduation_rate": self._extract_graduation_rate(**params.get("graduation_rate", {})),
            "student_faculty_ratio": self._extract_student_faculty_ratio(**params.get("student_faculty_ratio", {})),
            "average_class_size": self._extract_average_class_size(**params.get("average_class_size", {})),
            "tuition_per_credit": self._extract_tuition_per_credit(**params.get("tuition_per_credit", {})),
            "aid_percentage": self._extract_aid_percentage(**params.get("aid_percentage", {})),
        }
        compliance_flags = {
            "ferpa": self._check_ferpa(text),
            "title_ix": self._check_title_ix(text),
            "ada_section_504": self._check_ada_section_504(text),
            "accreditation": self._check_accreditation(text),
            "clery_act": self._check_clery_act(text),
        }
        risk_scores = {
            "academic_risk": self._score_academic_risk(text),
            "financial_risk": self._score_financial_risk(text),
            "compliance_risk": self._score_compliance_risk(text),
            "reputation_risk": self._score_reputation_risk(text),
            "operational_risk": self._score_operational_risk(text),
            "overall_risk": self._compute_overall_risk(text),
        }
        custom_rule_hits = _rk.check_custom_rules(text)

        return {
            "document_type": "unknown",
            "entities": entities,
            "metrics": metrics,
            "financials": {},
            "compliance_flags": compliance_flags,
            "risk_scores": risk_scores,
            "custom_rule_hits": custom_rule_hits,
            "text": text,
            "raw_text": text[:2000] if params.get("include_raw") else "",
            "metadata": {
                "extracted_at": self._timestamp(),
                "entity_count": sum(len(v) for v in entities.values()),
                "metric_count": sum(1 for v in metrics.values() if v and v.get("value") not in (None, [], "")),
                "institution_name": self._extract_institution_name(text),
            },
        }

    def _finalize_result(self, result: Dict, params: Dict) -> Dict:
        """Score confidence and strip working fields."""
        conf_report = assess_extraction_confidence(
            result,
            expected_fields=["entities", "metrics", "compliance_flags", "risk_scores"],
        )
        result["confidence"] = conf_report["overall"]
        result["confidence_report"] = conf_report
        result["metadata"]["confidence_threshold"] = params.get(
            "confidence_threshold", self.default_config["confidence_threshold"]
        )
        if "text" in result:
            del result["text"]
        return result

    def _extract_institution_name(self, text: str) -> Optional[str]:
        """Best-effort extraction of institution name."""
        pattern = r"(?:institution name|institution_name)[:\s]+([A-Z][A-Za-z0-9\s&.,-]{2,60})"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            return match.group(1).strip()
        return None

    # ------------------------------------------------------------------
    # ENTITY EXTRACTION (private)
    # ------------------------------------------------------------------

    def _extract_student_ids(self, text: str) -> List[Dict]:
        """Extract student ids from text."""
        found = []
        for match in re.finditer(r"(?:student\s*id|sis\s*number|student\s*number)\s*#?\s*(\d{6,12})", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "student_ids",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_course_codes(self, text: str) -> List[Dict]:
        """Extract course codes from text."""
        found = []
        for match in re.finditer(r"\b([A-Z]{2,4}\s*\d{3,4})\b", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "course_codes",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_credit_hours(self, text: str) -> List[Dict]:
        """Extract credit hours from text."""
        found = []
        for match in re.finditer(r"(\d+)\s*(?:credit|credits|credit hours|semester hour|quarter hour)", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "credit_hours",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_grades(self, text: str) -> List[Dict]:
        """Extract grades from text."""
        found = []
        for match in re.finditer(r"\b(A\+|A|A-|B\+|B|B-|C\+|C|C-|D|F|pass|fail|incomplete|withdrawal)\b", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "grades",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_instructors(self, text: str) -> List[Dict]:
        """Extract instructors from text."""
        found = []
        for match in re.finditer(r"(?:professor|instructor|lecturer|ta|adjunct|faculty)\s*[\-:]?\s*([A-Z][A-Za-z\s\.]+)", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "instructors",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_institutions(self, text: str) -> List[Dict]:
        """Extract institutions from text."""
        found = []
        for match in re.finditer(r"(?:university|college|school|academy|institute|district)\s*[\-:]?\s*([A-Z][A-Za-z0-9\s&.,]+(?:of\s+[A-Z][A-Za-z]+)?)", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "institutions",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_programs(self, text: str) -> List[Dict]:
        """Extract programs from text."""
        found = []
        for match in re.finditer(r"(?:program|major|minor|concentration|certificate|diploma)\s*(?:in\s+)?([A-Z][A-Za-z\s]+)", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "programs",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    def _extract_semesters(self, text: str) -> List[Dict]:
        """Extract semesters from text."""
        found = []
        for match in re.finditer(r"\b(Fall|Spring|Summer|Winter)\s*(20\d{2})\b|\b(20\d{2})\s*academic\s*year\b", text, re.IGNORECASE):
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                found.append({
                    "type": "semesters",
                    "value": value.strip(),
                    "confidence": 0.85,
                    "context": text[max(0, match.start() - 20):match.end() + 20],
                })
        return self._deduplicate_entities(found)

    # ------------------------------------------------------------------
    # METRICS & FORMULA EXTRACTION (private)
    # ------------------------------------------------------------------

    def _extract_gpa(self, grade_points=None, credit_hours=None) -> Dict[str, Any]:
        """Calculate gpa."""
        try:
            value = (grade_points / credit_hours) if credit_hours else None
            if value is None:
                return {"name": "gpa", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "gpa", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "gpa", "value": None, "inputs": {}, "error": str(e)}

    def _extract_completion_rate(self, completed_credits=None, attempted_credits=None) -> Dict[str, Any]:
        """Calculate completion rate."""
        try:
            value = (completed_credits / attempted_credits * 100) if attempted_credits else None
            if value is None:
                return {"name": "completion_rate", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "completion_rate", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "completion_rate", "value": None, "inputs": {}, "error": str(e)}

    def _extract_retention_rate(self, returned_students=None, previous_cohort=None) -> Dict[str, Any]:
        """Calculate retention rate."""
        try:
            value = (returned_students / previous_cohort * 100) if previous_cohort else None
            if value is None:
                return {"name": "retention_rate", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "retention_rate", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "retention_rate", "value": None, "inputs": {}, "error": str(e)}

    def _extract_graduation_rate(self, graduated=None, started=None) -> Dict[str, Any]:
        """Calculate graduation rate."""
        try:
            value = (graduated / started * 100) if started else None
            if value is None:
                return {"name": "graduation_rate", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "graduation_rate", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "graduation_rate", "value": None, "inputs": {}, "error": str(e)}

    def _extract_student_faculty_ratio(self, total_students=None, total_faculty=None) -> Dict[str, Any]:
        """Calculate student faculty ratio."""
        try:
            value = (total_students / total_faculty) if total_faculty else None
            if value is None:
                return {"name": "student_faculty_ratio", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "student_faculty_ratio", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "student_faculty_ratio", "value": None, "inputs": {}, "error": str(e)}

    def _extract_average_class_size(self, total_students=None, total_classes=None) -> Dict[str, Any]:
        """Calculate average class size."""
        try:
            value = (total_students / total_classes) if total_classes else None
            if value is None:
                return {"name": "average_class_size", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "average_class_size", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "average_class_size", "value": None, "inputs": {}, "error": str(e)}

    def _extract_tuition_per_credit(self, total_tuition=None, credits=None) -> Dict[str, Any]:
        """Calculate tuition per credit."""
        try:
            value = (total_tuition / credits) if credits else None
            if value is None:
                return {"name": "tuition_per_credit", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "tuition_per_credit", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "tuition_per_credit", "value": None, "inputs": {}, "error": str(e)}

    def _extract_aid_percentage(self, aid_received=None, total_cost=None) -> Dict[str, Any]:
        """Calculate aid percentage."""
        try:
            value = (aid_received / total_cost * 100) if total_cost else None
            if value is None:
                return {"name": "aid_percentage", "value": None, "inputs": {}, "error": "Insufficient inputs"}
            return {"name": "aid_percentage", "value": round(value, 2), "inputs": {k: v for k, v in locals().items() if k not in ("value", "self")}, "confidence": 0.85}
        except Exception as e:
            return {"name": "aid_percentage", "value": None, "inputs": {}, "error": str(e)}

    # ------------------------------------------------------------------
    # REGULATORY & COMPLIANCE CHECKING (private)
    # ------------------------------------------------------------------

    def _check_ferpa(self, text: str) -> Dict[str, Any]:
        """Check ferpa compliance."""
        found = [kw for kw in COMPLIANCE_KEYWORDS["ferpa"] if kw in text.lower()]
        return {
            "regulation": "ferpa",
            "detected": bool(found),
            "keywords_found": found,
            "confidence": round(min(1.0, len(found) / 3.0), 2) if found else 0.0,
        }

    def _check_title_ix(self, text: str) -> Dict[str, Any]:
        """Check title ix compliance."""
        found = [kw for kw in COMPLIANCE_KEYWORDS["title_ix"] if kw in text.lower()]
        return {
            "regulation": "title_ix",
            "detected": bool(found),
            "keywords_found": found,
            "confidence": round(min(1.0, len(found) / 3.0), 2) if found else 0.0,
        }

    def _check_ada_section_504(self, text: str) -> Dict[str, Any]:
        """Check ada section 504 compliance."""
        found = [kw for kw in COMPLIANCE_KEYWORDS["ada_section_504"] if kw in text.lower()]
        return {
            "regulation": "ada_section_504",
            "detected": bool(found),
            "keywords_found": found,
            "confidence": round(min(1.0, len(found) / 3.0), 2) if found else 0.0,
        }

    def _check_accreditation(self, text: str) -> Dict[str, Any]:
        """Check accreditation compliance."""
        found = [kw for kw in COMPLIANCE_KEYWORDS["accreditation"] if kw in text.lower()]
        return {
            "regulation": "accreditation",
            "detected": bool(found),
            "keywords_found": found,
            "confidence": round(min(1.0, len(found) / 3.0), 2) if found else 0.0,
        }

    def _check_clery_act(self, text: str) -> Dict[str, Any]:
        """Check clery act compliance."""
        found = [kw for kw in COMPLIANCE_KEYWORDS["clery_act"] if kw in text.lower()]
        return {
            "regulation": "clery_act",
            "detected": bool(found),
            "keywords_found": found,
            "confidence": round(min(1.0, len(found) / 3.0), 2) if found else 0.0,
        }

    # ------------------------------------------------------------------
    # RISK SCORING (private)
    # ------------------------------------------------------------------

    def _score_academic_risk(self, text: str) -> RiskScore:
        """Score academic risk."""
        data = _rk.check_risk_keywords(text).get("academic_risk", {})
        score = data.get("score", 0.0)
        indicators = data.get("indicators", [])
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return RiskScore(
            category="academic_risk",
            score=round(score, 2),
            level=level,
            indicators=indicators[:5],
            confidence=data.get("confidence", 0.0),
        )

    def _score_financial_risk(self, text: str) -> RiskScore:
        """Score financial risk."""
        data = _rk.check_risk_keywords(text).get("financial_risk", {})
        score = data.get("score", 0.0)
        indicators = data.get("indicators", [])
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return RiskScore(
            category="financial_risk",
            score=round(score, 2),
            level=level,
            indicators=indicators[:5],
            confidence=data.get("confidence", 0.0),
        )

    def _score_compliance_risk(self, text: str) -> RiskScore:
        """Score compliance risk."""
        data = _rk.check_risk_keywords(text).get("compliance_risk", {})
        score = data.get("score", 0.0)
        indicators = data.get("indicators", [])
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return RiskScore(
            category="compliance_risk",
            score=round(score, 2),
            level=level,
            indicators=indicators[:5],
            confidence=data.get("confidence", 0.0),
        )

    def _score_reputation_risk(self, text: str) -> RiskScore:
        """Score reputation risk."""
        data = _rk.check_risk_keywords(text).get("reputation_risk", {})
        score = data.get("score", 0.0)
        indicators = data.get("indicators", [])
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return RiskScore(
            category="reputation_risk",
            score=round(score, 2),
            level=level,
            indicators=indicators[:5],
            confidence=data.get("confidence", 0.0),
        )

    def _score_operational_risk(self, text: str) -> RiskScore:
        """Score operational risk."""
        data = _rk.check_risk_keywords(text).get("operational_risk", {})
        score = data.get("score", 0.0)
        indicators = data.get("indicators", [])
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return RiskScore(
            category="operational_risk",
            score=round(score, 2),
            level=level,
            indicators=indicators[:5],
            confidence=data.get("confidence", 0.0),
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _compute_overall_risk(self, text: str) -> RiskScore:
        """Compute overall risk from individual risk scores."""
        risks = _rk.check_risk_keywords(text)
        total = sum(r.get("score", 0.0) for r in risks.values())
        count = len(risks) or 1
        score = total / count
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return RiskScore(
            category="overall_risk",
            score=round(score, 2),
            level=level,
            indicators=[],
            confidence=round(min(1.0, score + 0.1), 2),
        )

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities by value."""
        seen = set()
        unique = []
        for e in entities:
            key = (e.get("type"), str(e.get("value", "")).strip().lower())
            if key[1] and key not in seen:
                seen.add(key)
                unique.append(e)
        return unique
