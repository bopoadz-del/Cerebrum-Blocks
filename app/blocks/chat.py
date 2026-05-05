"""Chat Block - AI Chat with DeepSeek API and Anthropic fallback"""

import json
import os
import re
import httpx
from typing import Any, Dict

from app.core.universal_base import UniversalBlock


class ChatBlock(UniversalBlock):
    """AI chat completions with DeepSeek API and typed I/O"""

    name = "chat"
    version = "2.0.0"
    description = "AI chat completions with DeepSeek API"
    layer = 2
    tags = ["ai", "core", "llm", "chat", "typed"]
    requires = []

    default_config = {
        "default_provider": "deepseek",
        "max_tokens": 2048,
        "temperature": 0.7
    }

    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Ask anything...",
            "multiline": True
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "text", "type": "markdown", "label": "Response"}
            ]
        },
        "quick_actions": [
            {"icon": "💡", "label": "Explain", "prompt": "Explain this in simple terms"},
            {"icon": "📝", "label": "Summarize", "prompt": "Summarize the key points"}
        ]
    }

    # Common construction keywords for offline fallback
    CONSTRUCTION_KEYWORDS = [
        "concrete", "steel", "rebar", "foundation", "slab", "beam", "column",
        "drawing", "quantity", "boq", "estimate", "cost", "schedule", "programme",
        "primavera", "bim", "ifc", "contract", "specification", "submittal",
        "rfi", "change order", "procurement", "safety", "qa", "qc", "inspection"
    ]

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Process chat request"""
        params = params or {}
        if isinstance(input_data, dict):
            message = (
                input_data.get("text") or
                input_data.get("content") or
                input_data.get("extracted_text") or
                str(input_data)
            )
        else:
            message = str(input_data)

        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        model = params.get("model", "deepseek-chat")
        max_tokens = params.get("max_tokens", self.config.get("max_tokens", 2048))
        temperature = params.get("temperature", self.config.get("temperature", 0.7))
        stream = params.get("stream", False)

        if not deepseek_key and not anthropic_key:
            return self._offline_response(message, "No AI provider configured. Set DEEPSEEK_API_KEY or ANTHROPIC_API_KEY environment variable.")

        # Try DeepSeek first, fall back to Anthropic Claude
        deepseek_error = ""
        if deepseek_key:
            result = await self._call_deepseek(message, model, max_tokens, temperature, stream, deepseek_key)
            if result.get("status") == "success":
                return result
            deepseek_error = result.get("error", "DeepSeek failed")
        else:
            deepseek_error = "DEEPSEEK_API_KEY not configured"

        if anthropic_key:
            result = await self._call_anthropic(message, max_tokens, temperature, anthropic_key, fallback_reason=deepseek_error)
            if result.get("status") == "success":
                return result
            anthropic_error = result.get("error", "Anthropic failed")
        else:
            anthropic_error = "ANTHROPIC_API_KEY not configured"

        # Both providers failed — check if it's a credit issue
        combined_error = f"{deepseek_error}. {anthropic_error}"
        return self._offline_response(message, combined_error)

    def _offline_response(self, message: str, error_detail: str) -> Dict:
        """Return a graceful offline response when all AI providers fail."""
        lower_msg = message.lower()
        is_credit_issue = any(k in error_detail.lower() for k in [
            "insufficient balance", "credit balance", "credit", "quota exceeded",
            "rate limit", "billing", "payment required"
        ])

        credit_notice = ""
        if is_credit_issue:
            credit_notice = (
                "\n\n⚠️ **AI service credits exhausted** — Both DeepSeek and Anthropic "
                "API keys are currently out of credits. The response below is generated "
                "locally by the Cerebrum platform using rule-based logic.\n\n---\n\n"
            )
        else:
            credit_notice = (
                "\n\n⚠️ **AI service unavailable** — "
                "The response below is generated locally by the Cerebrum platform.\n\n---\n\n"
            )

        # Try to give a useful rule-based response for construction queries
        fallback_text = self._generate_fallback_text(message)

        return {
            "status": "success",
            "text": credit_notice + fallback_text,
            "provider": "offline",
            "model": "cerebrum-local",
            "offline": True,
            "fallback": True,
            "fallback_reason": "credit_exhausted" if is_credit_issue else "providers_unavailable",
            "error_detail": error_detail,
            "credit_exhausted": is_credit_issue,
        }

    def _generate_fallback_text(self, message: str) -> str:
        """Generate a rule-based response for common construction queries."""
        lower = message.lower()

        # Quantity / estimation queries
        if any(k in lower for k in ["concrete volume", "how much concrete", "concrete quantity"]):
            return (
                "To calculate concrete volume, you need:\n"
                "- **Slab**: Length × Width × Thickness (all in same units)\n"
                "- **Beam**: Length × Width × Depth\n"
                "- **Column**: Height × Width × Depth × Number of columns\n"
                "\nAdd 5–10% wastage factor. For reinforced concrete, typical steel is 80–120 kg/m³."
            )
        if any(k in lower for k in ["steel weight", "rebar weight", "reinforcement weight"]):
            return (
                "Typical reinforcement ratios by element:\n"
                "- **Slabs**: 80–100 kg/m³ of concrete\n"
                "- **Beams**: 120–160 kg/m³\n"
                "- **Columns**: 150–200 kg/m³\n"
                "- **Foundations**: 80–120 kg/m³\n"
                "\nMultiply total concrete volume by the ratio for your element type."
            )
        if any(k in lower for k in ["cost estimate", "project cost", "building cost"]):
            return (
                "Typical construction costs (USD/m² of GFA):\n"
                "- **Residential (mid-range)**: $1,200–$1,800/m²\n"
                "- **Commercial office**: $1,500–$2,500/m²\n"
                "- **Industrial warehouse**: $800–$1,200/m²\n"
                "- **High-rise luxury**: $2,500–$4,000/m²\n"
                "\nAdd 10–15% for design fees, permits, and soft costs. Location and market conditions vary significantly."
            )
        if any(k in lower for k in ["primavera", "schedule", "cpm", "critical path"]):
            return (
                "For schedule analysis:\n"
                "1. Upload your XER or XML file to the Construction block\n"
                "2. The platform auto-calculates CPM and identifies the critical path\n"
                "3. Compare against baseline to detect delays\n"
                "4. Review recovery options (crash, fast-track, scope reduction)\n"
                "\nKey metrics: total float < 2 days = high risk."
            )
        if any(k in lower for k in ["bim", "ifc", "model"]):
            return (
                "BIM / IFC capabilities:\n"
                "- Upload `.ifc` files for automatic element extraction\n"
                "- Quantities: walls, columns, beams, slabs, openings\n"
                "- Compare as-built photos against BIM for progress tracking\n"
                "- Clash detection and spatial analysis (upcoming)\n"
                "\nSupported: IFC2X3, IFC4."
            )
        if any(k in lower for k in ["contract", "clause", "payment", "liquidated damages", "retention"]):
            return (
                "Common contract clauses to review:\n"
                "- **Payment terms**: milestone vs monthly, currency, advance payment %\n"
                "- **Liquidated Damages**: rate per day of delay, cap amount\n"
                "- **Retention**: typically 5–10%, released 50% at PC, 50% at final certificate\n"
                "- **Force Majeure**: defined events, notice period, time extension only\n"
                "- **Dispute resolution**: DAB, arbitration, or litigation\n"
                "\nUpload your contract PDF to the Construction block for automated clause extraction."
            )
        if any(k in lower for k in ["safety", "hazard", "risk"]):
            return (
                "Construction risk management:\n"
                "- **Design risks**: late information, design changes, coordination gaps\n"
                "- **Schedule risks**: weather, labour shortage, material delays\n"
                "- **Financial risks**: cash flow, price escalation, currency fluctuation\n"
                "- **Regulatory risks**: permit delays, authority approvals\n"
                "\nUse the Risk Register auto-populate feature in the Construction block to generate a full register from your documents."
            )
        if any(k in lower for k in ["submittal", "shop drawing", "material approval"]):
            return (
                "Submittal log essentials:\n"
                "- **Shop drawings**: structural steel, precast, MEP coordination\n"
                "- **Material submittals**: concrete mix, finishes, waterproofing membranes\n"
                "- **Method statements**: excavation, concrete pours, crane lifts\n"
                "- **Test certificates**: concrete cubes, steel mill certs, soil reports\n"
                "\nAllow 14 days for Engineer review per typical contract terms."
            )
        if any(k in lower for k in ["drawing", "qto", "quantity takeoff", "measurement"]):
            return (
                "Quantity take-off from drawings:\n"
                "1. Upload PDF drawings to the Construction block for auto-extraction\n"
                "2. For DXF files, use the Drawing QTO block for precise CAD measurements\n"
                "3. The platform extracts: linear dims, areas, counts, and schedules\n"
                "4. Results feed directly into BOQ and cost estimation\n"
                "\nTypical accuracy: ±5% for well-dimensioned drawings."
            )

        # Generic helpful response
        return (
            "I'm operating in **offline mode** right now because the AI service providers "
            "(DeepSeek / Anthropic) are unavailable or out of credits.\n\n"
            "I can still help with construction-specific queries using built-in knowledge. "
            "Try asking about:\n"
            "- Concrete or steel quantities\n"
            "- Cost estimation benchmarks\n"
            "- Schedule / Primavera analysis\n"
            "- Contract clause review\n"
            "- BIM / IFC processing\n"
            "- Risk management\n"
            "- Submittals and shop drawings\n"
            "- Quantity take-offs from drawings\n\n"
            "Or upload a document to the Construction block for automated analysis."
        )

    async def _call_deepseek(self, message: str, model: str, max_tokens: int, temperature: float, stream: bool, api_key: str) -> Dict:
        if stream:
            async def _stream_generator():
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "user", "content": message}],
                              "max_tokens": max_tokens, "temperature": temperature, "stream": True},
                    ) as response:
                        if response.status_code != 200:
                            err = await response.aread()
                            yield json.dumps({"type": "error", "message": f"DeepSeek error {response.status_code}: {err[:200]}"})
                            return
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue
            return {"status": "success", "text": "", "provider": "deepseek", "model": model, "stream": _stream_generator()}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": message}],
                          "max_tokens": max_tokens, "temperature": temperature},
                )
                if response.status_code != 200:
                    body = response.text[:500]
                    return {"status": "error", "error": f"DeepSeek API error (HTTP {response.status_code}): {body}"}
                data = response.json()
                return {"status": "success", "text": data["choices"][0]["message"]["content"],
                        "provider": "deepseek", "model": model, "tokens": data.get("usage", {})}
        except httpx.TimeoutException:
            return {"status": "error", "error": "DeepSeek request timed out"}
        except Exception as e:
            return {"status": "error", "error": f"DeepSeek failed: {str(e)}"}

    async def _call_anthropic(self, message: str, max_tokens: int, temperature: float, api_key: str, fallback_reason: str = "") -> Dict:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": message}],
            )
            text = response.content[0].text if response.content else ""
            return {
                "status": "success",
                "text": text,
                "provider": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "tokens": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
                "fallback_reason": fallback_reason or None,
            }
        except Exception as e:
            return {"status": "error", "error": f"Anthropic fallback also failed: {str(e)}"}
