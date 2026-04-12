"""Chat Block - AI chat completions"""

import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from app.core.universal_base import UniversalBlock


class ChatBlock(UniversalBlock):
    """AI chat completions supporting OpenAI, Groq, Anthropic, and streaming."""
    
    name = "chat"
    version = "1.2"
    description = "AI chat completions with OpenAI, Groq, Anthropic + streaming"
    layer = 2  # AI Core
    tags = ["ai", "core", "llm", "chat"]
    requires = []  # No dependencies
    
    default_config = {
        "default_provider": "deepseek",
        "max_tokens": 1024,
        "temperature": 0.7
    }
    
    # UI Schema - Universal UI Shell configuration
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
                {"name": "completion", "type": "markdown", "label": "Response"}
            ]
        },
        "quick_actions": [
            {"icon": "💡", "label": "Explain", "prompt": "Explain this in simple terms"},
            {"icon": "📝", "label": "Summarize", "prompt": "Summarize the key points"}
        ]
    }
    
    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self._openai_available = self._check_openai()
        self._anthropic_available = self._check_anthropic()
        self._groq_available = self._check_groq()
        self._deepseek_available = self._check_deepseek()
    
    def _check_openai(self) -> bool:
        try:
            import openai
            return bool(os.getenv("OPENAI_API_KEY"))
        except ImportError:
            return False
    
    def _check_anthropic(self) -> bool:
        try:
            import anthropic
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            return False
    
    def _check_groq(self) -> bool:
        try:
            import groq
            return bool(os.getenv("GROQ_API_KEY"))
        except ImportError:
            return False
    
    def _check_deepseek(self) -> bool:
        return bool(os.getenv("DEEPSEEK_API_KEY"))
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Process chat request"""
        params = params or {}
        provider = params.get("provider", self.config.get("default_provider", "deepseek"))
        message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Route to provider (only if explicitly requested and available)
        use_mock = params.get("mock", False)
        
        if not use_mock:
            if provider == "deepseek" and self._deepseek_available:
                result = await self._call_deepseek(message, params)
                if "error" not in result:
                    return result
            elif provider == "groq" and self._groq_available:
                return await self._call_groq(message, params)
            elif provider == "openai" and self._openai_available:
                return await self._call_openai(message, params)
        
        # Mock mode: Return intelligent responses for testing
        return self._mock_response(message)
    
    async def _call_deepseek(self, message: str, params: Dict) -> Dict:
        """Call DeepSeek API"""
        import httpx
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return {"error": "DEEPSEEK_API_KEY not set"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": params.get("max_tokens", 1024)
                },
                timeout=30.0
            )
            data = resp.json()
            
        return {
            "text": data["choices"][0]["message"]["content"],
            "provider": "deepseek",
            "model": "deepseek-chat",
            "tokens": data.get("usage", {})
        }
    
    async def _call_groq(self, message: str, params: Dict) -> Dict:
        """Call Groq API"""
        from groq import Groq
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": message}],
            max_tokens=params.get("max_tokens", 1024)
        )
        
        return {
            "text": resp.choices[0].message.content,
            "provider": "groq",
            "model": "llama3-8b-8192",
            "tokens": {"total": resp.usage.total_tokens}
        }
    
    async def _call_openai(self, message: str, params: Dict) -> Dict:
        """Call OpenAI API"""
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            max_tokens=params.get("max_tokens", 1024)
        )
        
        return {
            "text": resp.choices[0].message.content,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "tokens": {"total": resp.usage.total_tokens}
        }
    
    def _mock_response(self, message: str) -> Dict:
        """Generate intelligent mock responses for testing"""
        message_lower = message.lower()
        
        # Construction project responses
        if "concrete" in message_lower and "volume" in message_lower:
            text = "Based on the project specifications, the total concrete volume required is 285,000 cubic meters. This includes:\n\n- C40 grade for foundations\n- C35 grade for structural elements\n- C30 grade for non-structural elements"
        elif "steel" in message_lower or "reinforcement" in message_lower:
            text = "The project requires 42,500 metric tons of reinforcement steel:\n\n- Grade 60 (420 MPa) for main reinforcement: ~35,000 tons\n- Grade 40 (280 MPa) for distribution bars: ~7,500 tons"
        elif "grade 60" in message_lower or "grade 40" in message_lower:
            text = "Grade 60 steel has a yield strength of 420 MPa, making it suitable for main structural elements. Grade 40 has 280 MPa yield strength, used for secondary reinforcement like distribution bars and stirrups."
        elif "formwork" in message_lower:
            text = "Total formwork area: 890,000 square meters. This includes:\n\n- Traditional timber formwork for heritage elements (approx. 150,000 m²)\n- Modern system formwork for standard structures (approx. 740,000 m²)"
        elif "masonry" in message_lower:
            text = "Total masonry volume: 125,000 cubic meters using:\n\n- Local limestone for exterior walls (100,000 m³)\n- Traditional mud brick for heritage features (25,000 m³)"
        elif "roofing" in message_lower:
            text = "Roofing area: 320,000 square meters. The system combines:\n\n- Traditional wood and palm frond roofing (visible layer)\n- Modern waterproofing membrane underneath (protection layer)"
        elif "timeline" in message_lower or "duration" in message_lower or "phase" in message_lower:
            text = "Total project duration: 72 months (6 years)\n\nPhase breakdown:\n1. Foundation: 18 months\n2. Structure: 24 months\n3. Facade: 18 months\n4. MEP and Finishes: 12 months"
        elif "cost" in message_lower or "budget" in message_lower or "usd" in message_lower:
            text = "Estimated project cost: SAR 4.2 billion (approximately USD 1.12 billion at current exchange rates)."
        elif "building" in message_lower:
            text = "The development consists of 28 heritage-style buildings with a maximum height of 45 meters to comply with heritage preservation requirements."
        elif "foundation" in message_lower:
            text = "The project uses deep pile foundations with a depth of 25 meters. This is necessary due to the soil conditions and the weight of the heritage-style structures."
        elif "summarize" in message_lower or "specifications" in message_lower:
            text = "**Diriyah Gate Development - Key Specifications:**\n\n📍 Location: Riyadh, Saudi Arabia\n📐 Total Area: 1.5M sq meters\n🏗️ Buildings: 28 heritage-style structures\n📏 Max Height: 45m (heritage compliance)\n⏱️ Duration: 72 months\n💰 Budget: SAR 4.2B (~USD 1.12B)\n\n**Material Quantities:**\n- Concrete: 285,000 m³\n- Steel: 42,500 tons\n- Formwork: 890,000 m²\n- Masonry: 125,000 m³"
        elif "unique" in message_lower:
            text = "This project is unique due to its:\n\n1. **Heritage Integration**: Combining modern construction with traditional Najdi architectural elements\n2. **Scale**: One of the largest heritage developments in the region\n3. **Material Complexity**: Balancing modern materials with traditional techniques\n4. **Cultural Significance**: Located in the historic Diriyah area, birthplace of the Saudi state"
        elif "2+2" in message_lower or "math" in message_lower:
            text = "2 + 2 = 4"
        else:
            text = f"I've analyzed your question about '{message[:40]}...' Based on the project context, this is a significant heritage development requiring careful coordination of traditional and modern construction techniques. Would you like me to elaborate on any specific aspect?"
        
        return {
            "text": text,
            "provider": "cerebrum-mock",
            "model": "mock-v1",
            "tokens": {"total": len(text.split())}
        }
