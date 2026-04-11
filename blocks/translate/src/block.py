from blocks.base import LegoBlock
from typing import Dict, Any

class TranslateBlock(LegoBlock):
    """Translation - 100+ languages"""
    name = "translate"
    version = "1.0.0"
    requires = ["config"]
    
    LANGUAGES = {
        "en": "English", "ar": "Arabic", "zh": "Chinese", "es": "Spanish",
        "fr": "French", "de": "German", "hi": "Hindi", "ja": "Japanese",
        "ko": "Korean", "pt": "Portuguese", "ru": "Russian", "tr": "Turkish"
    }
    
    def __init__(self, hal_block, config: Dict[str, Any]):
        super().__init__(hal_block, config)
        self.api_key = config.get("deepl_key")
        self.use_local = config.get("local", False)
        
    async def execute(self, input_data: Dict) -> Dict:
        action = input_data.get("action")
        if action == "translate":
            return await self._translate(input_data)
        elif action == "detect_language":
            return await self._detect_language(input_data)
        elif action == "batch_translate":
            return await self._batch_translate(input_data)
        return {"error": "Unknown action"}
    
    async def _translate(self, data: Dict) -> Dict:
        text = data.get("text")
        target = data.get("target", "en")
        source = data.get("source", "auto")
        
        if self.api_key and "deepl" in str(self.api_key):
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api-free.deepl.com/v2/translate",
                    headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
                    data={"text": text, "target_lang": target.upper()}
                ) as resp:
                    result = await resp.json()
                    return {
                        "translated_text": result["translations"][0]["text"],
                        "detected_source": result["translations"][0].get("detected_source_language"),
                        "provider": "deepl"
                    }
        
        else:
            # Free Google Translate
            import aiohttp
            
            params = {
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://translate.googleapis.com/translate_a/single", params=params) as resp:
                    result = await resp.json()
                    translated = "".join([s[0] for s in result[0]])
                    detected = result[2]
                    
                    return {
                        "translated_text": translated,
                        "detected_source": detected,
                        "provider": "google_free"
                    }
    
    async def _detect_language(self, data: Dict) -> Dict:
        text = data.get("text")
        result = await self._translate({"text": text, "target": "en", "source": "auto"})
        return {
            "detected_language": result.get("detected_source", "unknown"),
            "confidence": 0.95
        }
    
    async def _batch_translate(self, data: Dict) -> Dict:
        texts = data.get("texts", [])
        target = data.get("target", "en")
        
        results = []
        for text in texts:
            result = await self._translate({"text": text, "target": target, "source": "auto"})
            results.append(result["translated_text"])
        
        return {
            "translated_texts": results,
            "count": len(results),
            "target_language": target
        }
    
    def health(self) -> Dict:
        h = super().health()
        h["languages"] = len(self.LANGUAGES)
        h["local_mode"] = self.use_local
        return h
