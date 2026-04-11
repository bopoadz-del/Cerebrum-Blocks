# Domain Container Specification v1.0
## The Cerebrum Domain Adapter Protocol (DAP)

---

## 🎯 Overview

**Cerebrum Blocks is not a product. It is an AI Operating System.**

Five layers are universal and never change. One layer is your product.

```
Layer 0  Infrastructure    ← HAL, Config, Memory, Database    [UNIVERSAL]
Layer 1  Security          ← Auth, Secrets, Rate Limiter      [UNIVERSAL]
Layer 2  AI Core           ← Router, Failover, Leaderboard    [UNIVERSAL]
Layer 3  [YOUR DOMAIN]     ← Construction, Medical, Legal     [YOUR PRODUCT]
Layer 4  Store             ← Discovery, Reviews, Payments     [UNIVERSAL]
Layer 5  Event Bus         ← Cross-container messaging        [UNIVERSAL]
```

**One container swap = new industry vertical.**

---

## 💰 Economics

| Domain Pack | Price | Platform (20%) | Creator (80%) |
|-------------|-------|----------------|---------------|
| Construction | $299/mo | $59.80 | $239.20 |
| Medical | $499/mo | $99.80 | $399.20 |
| Legal | $399/mo | $79.80 | $319.20 |
| Finance | $599/mo | $119.80 | $479.20 |

**You build once (Construction). Others build the rest. You collect the Lego Tax on every sale.**

---

## 📋 Required Interface

Every Domain Container MUST implement these 5 methods:

### 1. `process_document()` — Ingest Domain Files

```python
async def process_document(
    self, 
    input_data: Union[str, bytes, Dict],
    params: Dict
) -> Dict:
    """
    Ingest and parse domain-specific files.
    
    Args:
        input_data: File URL, raw bytes, or document metadata
        params: {
            "file_type": "pdf|dwg|dicom|xml|csv|...",
            "extract_mode": "full|metadata|entities",
            "language": "en"
        }
    
    Returns:
        {
            "status": "success|error|partial",
            "document_id": "doc_abc123",
            "extracted_data": {...},
            "confidence": 0.94,
            "processing_time_ms": 1450
        }
    """
```

**Examples:**
- **Construction:** PDF blueprints → extract measurements, material specs
- **Medical:** DICOM scans → identify anomalies, measurements
- **Legal:** Case files → extract parties, dates, precedents
- **Finance:** Trading data → pattern detection, risk metrics

---

### 2. `extract_entities()` — Domain-Specific Extraction

```python
async def extract_entities(
    self,
    input_data: Dict,
    params: Dict
) -> Dict:
    """
    Extract domain entities with relationships.
    
    Args:
        input_data: Output from process_document()
        params: {
            "entity_types": ["list", "of", "types"],
            "include_relationships": true,
            "confidence_threshold": 0.85
        }
    
    Returns:
        {
            "entities": [
                {
                    "id": "ent_001",
                    "type": "beam|patient|contract|trade",
                    "attributes": {...},
                    "confidence": 0.96,
                    "relationships": [{"to": "ent_002", "type": "supports"}]
                }
            ],
            "entity_count": 42
        }
    """
```

**Examples:**
- **Construction:** Beams, columns, materials, quantities
- **Medical:** Patients, symptoms, diagnoses, medications
- **Legal:** Parties, clauses, obligations, precedents
- **Finance:** Trades, positions, risk factors, counterparties

---

### 3. `validate()` — Domain Rules Compliance

```python
async def validate(
    self,
    input_data: Dict,
    params: Dict
) -> Dict:
    """
    Validate against domain standards and regulations.
    
    Args:
        input_data: Output from extract_entities()
        params: {
            "standard": "ACI318|HIPAA|SOX|GDPR",
            "strictness": "strict|moderate|lenient",
            "auto_fix": false
        }
    
    Returns:
        {
            "valid": true|false,
            "violations": [
                {
                    "rule": "beam_span_exceeded",
                    "severity": "critical|warning|info",
                    "entity": "ent_005",
                    "message": "Beam span exceeds 30ft without support",
                    "auto_fix_available": true
                }
            ],
            "compliance_score": 0.87
        }
    """
```

**Examples:**
- **Construction:** Building code compliance (ACI, AISC, local)
- **Medical:** HIPAA, FDA, clinical protocol compliance
- **Legal:** Contract enforceability, precedent alignment
- **Finance:** SOX, MiFID, risk limit compliance

---

### 4. `generate_report()` — Domain Output Format

```python
async def generate_report(
    self,
    input_data: Dict,
    params: Dict
) -> Dict:
    """
    Generate domain-standard deliverables.
    
    Args:
        input_data: Aggregated results from previous steps
        params: {
            "format": "pdf|json|xml|csv|xlsx",
            "template": "summary|detailed|executive",
            "include_charts": true,
            "language": "en"
        }
    
    Returns:
        {
            "report_id": "rpt_xyz789",
            "format": "pdf",
            "url": "https://storage.../report.pdf",
            "pages": 12,
            "generated_at": "2026-04-11T17:00:00Z",
            "expires_at": "2026-05-11T17:00:00Z"
        }
    """
```

**Examples:**
- **Construction:** BOQ (Bill of Quantities), inspection reports
- **Medical:** Clinical summaries, radiology reports
- **Legal:** Briefs, contract summaries, case analyses
- **Finance:** Risk reports, compliance filings, trade summaries

---

### 5. `health_check()` — Standard Interface

```python
async def health_check(self) -> Dict:
    """
    Return container health status.
    
    Returns:
        {
            "status": "healthy|degraded|unhealthy",
            "version": "1.0.0",
            "capabilities": [
                "process_document",
                "extract_entities", 
                "validate",
                "generate_report"
            ],
            "domain": "construction|medical|legal|finance",
            "dependencies": {
                "database": "connected",
                "ai_providers": ["deepseek", "groq"],
                "external_apis": "available"
            }
        }
    """
```

---

## 🏗️ Base Class Template

Copy this to create your Domain Container:

```python
from typing import Any, Dict, Union
from app.core.base import BaseBlock, BlockConfig

class DomainContainer(BaseBlock):
    """
    [DOMAIN] Container for Cerebrum Blocks
    Domain: [construction|medical|legal|finance|...]
    Version: 1.0.0
    """
    
    def __init__(self):
        super().__init__(BlockConfig(
            name="[domain]",  # e.g., "medical", "legal"
            version="1.0.0",
            description="[Domain] Container: [brief description]",
            supported_inputs=["pdf", "xml", "json", "..."],
            supported_outputs=["report", "entities", "validation"],
            layer=3  # Domain layer
        ))
        # Initialize domain-specific models, databases, etc.
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """
        Main entry point. Routes to appropriate method based on action.
        """
        params = params or {}
        action = params.get("action", "process_document")
        
        if action == "process_document":
            return await self.process_document(input_data, params)
        elif action == "extract_entities":
            return await self.extract_entities(input_data, params)
        elif action == "validate":
            return await self.validate(input_data, params)
        elif action == "generate_report":
            return await self.generate_report(input_data, params)
        elif action == "health_check":
            return await self.health_check()
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "process_document",
                    "extract_entities",
                    "validate",
                    "generate_report",
                    "health_check"
                ]
            }
    
    # Implement the 5 required methods here...
    # async def process_document(self, input_data, params): ...
    # async def extract_entities(self, input_data, params): ...
    # async def validate(self, input_data, params): ...
    # async def generate_report(self, input_data, params): ...
    # async def health_check(self): ...
```

---

## 🔌 Registration

Add your container to the platform:

```python
# In app/main.py or app/containers/__init__.py
from .containers.your_domain import DomainContainer

BLOCK_REGISTRY = {
    # ... existing blocks ...
    "your_domain": DomainContainer,
}
```

---

## ✅ Certification Checklist

Before submitting to the Block Store, verify:

- [ ] All 5 methods implemented
- [ ] Returns standardized response format
- [ ] Includes confidence scores (0.0-1.0)
- [ ] Error handling with clear messages
- [ ] No hardcoded secrets or credentials
- [ ] Health check returns accurate status
- [ ] Processing time under 5 seconds (standard) or 30 seconds (large docs)
- [ ] Documentation includes domain glossary
- [ ] Example requests/responses provided

---

## 📝 Submission to Block Store

```json
POST https://ssdppg.onrender.com/execute
{
  "block": "store",
  "params": {
    "action": "publish",
    "name": "medical_container",
    "display_name": "Medical AI Pack",
    "domain": "healthcare",
    "price_cents": 49900,
    "description": "HIPAA-compliant medical document processing",
    "capabilities": [
      "DICOM processing",
      "Entity extraction (patients, symptoms)",
      "HIPAA validation",
      "Clinical report generation"
    ],
    "author": "your_name",
    "repository": "https://github.com/..."
  }
}
```

---

## 🌐 Domain Examples

### Construction (Built)
```python
actions = [
    "extract_measurements",    # BOQ generation
    "qa_inspection",          # Defect detection
    "progress_tracking",      # Schedule vs actual
    "bim_analysis"           # IFC/DWG processing
]
standards = ["ACI318", "AISC360", "OSHA"]
```

### Medical (Template)
```python
actions = [
    "process_dicom",          # Scan ingestion
    "extract_findings",       # Anomaly detection
    "validate_hipaa",         # Compliance check
    "generate_clinical_summary"
]
standards = ["HIPAA", "DICOM", "HL7"]
```

### Legal (Template)
```python
actions = [
    "process_contract",       # Document ingestion
    "extract_clauses",        # Clause identification
    "validate_precedent",     # Case law check
    "generate_brief"         # Legal brief
]
standards = ["ABA", "Bluebook", "Local Rules"]
```

### Finance (Template)
```python
actions = [
    "process_trades",         # Trade data ingestion
    "extract_risk_factors",   # Risk analysis
    "validate_compliance",    # SOX/MiFID check
    "generate_risk_report"    # Risk report
]
standards = ["SOX", "MiFID II", "Basel III"]
```

---

## 🔄 Chain Integration

Domain containers work in multi-block chains:

```json
{
  "steps": [
    {"block": "security", "params": {"action": "auth"}},
    {"block": "medical", "params": {"action": "process_dicom"}},
    {"block": "ai_core", "params": {"action": "route"}},
    {"block": "medical", "params": {"action": "extract_findings"}},
    {"block": "medical", "params": {"action": "generate_report"}}
  ]
}
```

---

## 🎓 Best Practices

1. **Confidence Scores:** Always return confidence (0.0-1.0). Users need to know when to verify.

2. **Idempotency:** Same input → same output. Store document hashes to avoid reprocessing.

3. **Async Processing:** Large files should return `status: "pending"` with a job ID.

4. **Error Context:** Don't just say "failed." Say "Beam span calculation failed: missing concrete grade."

5. **Audit Trail:** Log every action through the Event Bus for compliance.

6. **Rate Limit Awareness:** Check `X-RateLimit-Remaining` header. Back off if low.

7. **Provider Fallback:** If DeepSeek fails, try Groq. Don't fail the user.

---

## 📚 Additional Resources

- **API Reference:** `API.md`
- **Security Guidelines:** Layer 1 enforces auth. Don't bypass.
- **Event Bus Docs:** Cross-container messaging protocol
- **Example Implementations:**
  - `app/containers/construction.py` (reference)
  - `app/containers/medical.py` (template - stub)
  - `app/containers/legal.py` (template - stub)

---

## 🚀 Getting Started

1. Copy the Base Class Template
2. Implement the 5 required methods for your domain
3. Test locally with `pytest tests/test_domain.py`
4. Submit to Block Store
5. Collect 80% of revenue (20% to platform)

---

**Version:** 1.0.0  
**Last Updated:** 2026-04-11  
**Status:** ✅ ACTIVE — Submit domain containers now

---

*The Domain Adapter Protocol turns every industry vertical into a product opportunity. One container swap. Infinite markets.*
