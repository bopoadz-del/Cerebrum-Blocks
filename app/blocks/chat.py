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
        """Process chat request using real AI APIs"""
        params = params or {}
        provider = params.get("provider", self.config.get("default_provider", "deepseek"))
        message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Check env vars directly (not cached)
        deepseek_available = bool(os.getenv("DEEPSEEK_API_KEY"))
        groq_available = bool(os.getenv("GROQ_API_KEY"))
        openai_available = bool(os.getenv("OPENAI_API_KEY"))
        
        # Route to available provider
        if provider == "deepseek" and deepseek_available:
            result = await self._call_deepseek(message, params)
            if "error" not in result:
                return result
        
        if provider == "groq" and groq_available:
            return await self._call_groq(message, params)
        
        if provider == "openai" and openai_available:
            return await self._call_openai(message, params)
        
        # No API available - return error
        return {
            "status": "error",
            "error": "No AI API available. Please set DEEPSEEK_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY environment variable."
        }
    
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
        message_lower = message.lower().strip()
        
        # Greetings & small talk
        if message_lower in ["hi", "hello", "hey", "greetings"]:
            text = "Hello! I'm your construction AI assistant. I can help you analyze project specifications, calculate material quantities, review timelines, and answer questions about the Diriyah Gate Development or any construction project. What would you like to know?"
        elif message_lower in ["yes", "yeah", "sure", "ok", "okay"]:
            text = "Great! Here are some things I can help you with:\n\n📊 **Material Quantities** - Concrete, steel, formwork calculations\n📅 **Project Timeline** - Phase breakdowns and scheduling\n💰 **Cost Analysis** - Budget estimates and cost breakdowns\n🏗️ **Technical Specs** - Foundation, structural, architectural details\n📋 **Compliance** - Building codes and heritage requirements\n\nWhat specific aspect would you like to explore?"
        elif message_lower in ["no", "nope", "nah"]:
            text = "No problem! Feel free to ask me anything about your construction project whenever you're ready. I'm here to help with material calculations, timeline planning, cost estimates, and technical specifications."
        elif "elaborate" in message_lower or "tell me more" in message_lower or "explain" in message_lower:
            text = "I'd be happy to elaborate! Here are the key details about this project:\n\n**Diriyah Gate Development** is a flagship heritage project in Riyadh that combines traditional Najdi architecture with modern construction techniques. The development spans 1.5 million square meters and includes 28 buildings designed to reflect the historic character of the Diriyah area.\n\nThe project uses specialized materials including traditional mud bricks and local limestone alongside modern concrete and steel systems. The 72-month construction timeline is carefully phased to minimize disruption while maintaining quality standards.\n\nWhat specific aspect would you like me to dive deeper into?"
        elif "thank" in message_lower:
            text = "You're welcome! I'm here to help with any construction-related questions. Feel free to upload documents, ask about specific materials, or request detailed analysis anytime."
        elif "help" in message_lower:
            text = "I can assist you with:\n\n📁 **Document Analysis** - Upload PDFs, specs, or drawings\n📊 **Material Calculations** - Concrete, steel, formwork quantities\n📅 **Timeline Planning** - Phase breakdowns and scheduling\n💰 **Cost Estimation** - Budget analysis and pricing\n🔍 **Technical Review** - Specifications and compliance\n❓ **Q&A** - Ask me anything about your project\n\nWhat do you need help with?"
        
        # Construction project responses
        elif "concrete" in message_lower and "volume" in message_lower:
            text = "Based on the project specifications, the total concrete volume required is **285,000 cubic meters**. This breaks down as:\n\n• **C40 Grade** (Foundations): 95,000 m³\n• **C35 Grade** (Columns/Beams): 125,000 m³\n• **C30 Grade** (Slabs/Non-structural): 65,000 m³\n\nThis volume supports 28 heritage-style buildings across 1.5 million square meters of development area."
        elif "steel" in message_lower or "reinforcement" in message_lower:
            text = "The project requires **42,500 metric tons** of reinforcement steel:\n\n• **Grade 60 (420 MPa)** - Main reinforcement: 35,000 tons\n  - Used for: Columns, beams, primary structural elements\n  - Standard: ASTM A615 Grade 60\n\n• **Grade 40 (280 MPa)** - Distribution bars: 7,500 tons\n  - Used for: Stirrups, distribution bars, secondary elements\n  - Standard: ASTM A615 Grade 40"
        elif "grade 60" in message_lower or "grade 40" in message_lower:
            text = "**Grade 60 vs Grade 40 Steel:**\n\n**Grade 60 (420 MPa):**\n- Yield strength: 420 MPa\n- Tensile strength: 620 MPa minimum\n- Used for: Main structural elements, columns, beams\n- Higher strength allows for less steel volume\n\n**Grade 40 (280 MPa):**\n- Yield strength: 280 MPa\n- Used for: Distribution bars, stirrups, secondary elements\n- More economical for non-critical reinforcement\n\nThis project uses 35,000 tons of Grade 60 and 7,500 tons of Grade 40."
        elif "formwork" in message_lower:
            text = "Total formwork area required: **890,000 square meters**\n\n• **Traditional Timber** (Heritage elements): 150,000 m²\n  - Hand-crafted wooden forms\n  - Used for decorative heritage features\n  - Higher labor but authentic aesthetic\n\n• **Modern System Formwork** (Standard structures): 740,000 m²\n  - Aluminum panel systems\n  - Faster installation and reuse\n  - Cost-effective for repetitive elements"
        elif "masonry" in message_lower:
            text = "Total masonry volume: **125,000 cubic meters**\n\n• **Local Limestone**: 100,000 m³\n  - Source: Turaif quarries\n  - Application: Exterior walls, heritage facades\n  - Authentic to Najdi architecture\n\n• **Traditional Mud Brick**: 25,000 m³\n  - Mix: 40% clay, 30% sand, 30% straw\n  - Application: Decorative heritage features\n  - Traditional cooling properties"
        elif "roofing" in message_lower:
            text = "Roofing area: **320,000 square meters**\n\nThe system uses a dual-layer approach:\n\n• **Visible Layer**: Traditional wood & palm frond roofing\n  - Authentic Najdi appearance\n  - Natural ventilation properties\n  - Requires skilled traditional craftsmen\n\n• **Protection Layer**: Modern waterproofing membrane\n  - EPDM membrane, 1.5mm thickness\n  - 20-year warranty\n  - Prevents water infiltration"
        elif "timeline" in message_lower or "duration" in message_lower or "phase" in message_lower:
            text = "**Total Project Duration: 72 months (6 years)**\n\n**Phase Breakdown:**\n\n1️⃣ **Foundation** (18 months)\n   - Piling works: 8 months\n   - Pile caps & ground beams: 10 months\n\n2️⃣ **Structure** (24 months)\n   - Columns & shear walls: 10 months\n   - Floor slabs: 8 months\n   - Roof structure: 6 months\n\n3️⃣ **Facade** (18 months)\n   - Masonry works: 12 months\n   - Traditional finishes: 6 months\n\n4️⃣ **MEP & Finishes** (12 months)\n   - Mechanical/Electrical: 8 months\n   - Interior finishes: 4 months"
        elif "cost" in message_lower or "budget" in message_lower or "usd" in message_lower or "price" in message_lower:
            text = "**Project Budget Summary:**\n\n• **Total Cost**: SAR 4.2 billion\n• **USD Equivalent**: ~$1.12 billion (at 3.75 SAR/USD)\n• **Cost per m²**: SAR 13,125 (~$3,500)\n\n**Major Cost Components:**\n• Concrete (285,000 m³): ~SAR 855M\n• Steel (42,500 tons): ~SAR 765M\n• Formwork (890,000 m²): ~SAR 445M\n• Masonry (125,000 m³): ~SAR 375M\n• Specialized heritage work: ~SAR 1.2B\n• MEP systems: ~SAR 840M\n\nNote: Costs are estimates based on current market rates."
        elif "building" in message_lower and ("count" in message_lower or "number" in message_lower or "many" in message_lower):
            text = "The development consists of **28 heritage-style buildings**.\n\n**Building Characteristics:**\n• Architecture: Traditional Najdi style\n• Maximum height: 45 meters (heritage compliance)\n• Total floor area: 320,000 square meters\n• Building footprint: 450,000 square meters\n• Site area: 1,500,000 square meters\n\nEach building incorporates traditional mud-brick aesthetics while meeting modern safety and comfort standards."
        elif "foundation" in message_lower:
            text = "**Foundation System: Deep Pile Foundation**\n\n**Specifications:**\n• Type: Cast-in-place reinforced concrete piles\n• Depth: 25 meters below ground level\n• Diameter: 1.2 meters\n• Quantity: 1,850 piles\n• Design load: 15,000 kN per pile\n• Pile cap system: Reinforced concrete raft\n\n**Why deep piles?**\n• Soil conditions in Riyadh require deep foundations\n• Heritage structures are heavy (thick walls)\n• Must resist seismic loads (Zone 2A)\n• Prevents differential settlement\n\nThis system ensures stability for the 45-meter tall heritage buildings."
        elif "summarize" in message_lower or "summary" in message_lower or "overview" in message_lower:
            text = "**Diriyah Gate Development - Project Summary**\n\n📍 **Location**: Riyadh, Saudi Arabia\n🏗️ **Client**: Diriyah Gate Development Authority\n👷 **Contractor**: Saudi Binladin Group\n\n📐 **Scale:**\n• Site area: 1.5 million m²\n• Buildings: 28 heritage structures\n• Floor area: 320,000 m²\n• Max height: 45m (heritage compliance)\n\n⏱️ **Timeline**: 72 months (6 years)\n💰 **Budget**: SAR 4.2B (~$1.12B USD)\n\n📊 **Key Materials:**\n• Concrete: 285,000 m³\n• Steel: 42,500 tons\n• Formwork: 890,000 m²\n• Masonry: 125,000 m³\n\n🎯 **Special Features:**\nTraditional Najdi architecture with modern construction techniques"
        elif "unique" in message_lower or "special" in message_lower:
            text = "**What Makes This Project Unique:**\n\n1️⃣ **Heritage Integration**\n   - Combines modern construction with traditional Najdi architecture\n   - Authentic mud-brick aesthetics using modern materials\n\n2️⃣ **Scale & Significance**\n   - One of the largest heritage developments in the region\n   - Located in historic Diriyah (birthplace of Saudi state)\n\n3️⃣ **Material Innovation**\n   - Balancing traditional materials (limestone, mud brick) with modern systems\n   - Specialized formwork for heritage detailing\n\n4️⃣ **Cultural Authenticity**\n   - Traditional palm frond roofing with modern waterproofing\n   - Skilled craftsman training for heritage techniques\n\n5️⃣ **Sustainability**\n   - Natural cooling properties of traditional materials\n   - Local sourcing reduces carbon footprint"
        elif "2+2" in message_lower or "math" in message_lower:
            text = "2 + 2 = 4"
        elif "who are you" in message_lower or "what are you" in message_lower:
            text = "I'm Cerebrum, your construction AI assistant! I'm designed to help with:\n\n• Analyzing construction documents and drawings\n• Calculating material quantities\n• Reviewing project timelines\n• Providing technical specifications\n• Answering questions about building codes\n• Assisting with cost estimation\n\nI work best when you upload project documents or ask specific questions about materials, timelines, or technical details. How can I help you today?"
        else:
            # Better fallback that acknowledges the question
            if len(message) < 20:
                text = f"I see you said '{message}'. I'm ready to help with your construction project! Ask me about material quantities, timelines, costs, or upload a document for analysis."
            else:
                text = f"I understand you're asking about '{message[:50]}...' To give you the best answer, could you be more specific? For example, I can help with:\n\n• Concrete/steel quantities\n• Project timeline breakdown\n• Cost estimates\n• Technical specifications\n• Building code requirements\n\nWhat would you like to know?"
        
        return {
            "text": text,
            "provider": "cerebrum-mock",
            "model": "mock-v1",
            "tokens": {"total": len(text.split())}
        }
