"""Voice Block - TTS and STT"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class VoiceBlock(UniversalBlock):
    """Text-to-Speech and Speech-to-Text"""
    
    name = "voice"
    version = "1.0"
    layer = 3
    tags = ["domain", "audio", "tts", "stt"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "audio",
            "accept": [".mp3", ".wav", ".webm", ".m4a"],
            "placeholder": "Record or upload audio...",
            "multiline": False
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "text", "type": "text", "label": "Transcription"}
            ]
        },
        "quick_actions": [
            {"icon": "🎤", "label": "Record Voice", "prompt": ""},
            {"icon": "🔊", "label": "Text to Speech", "prompt": "Convert this to speech"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Convert text to speech or vice versa"""
        action = (params or {}).get("action", "tts")
        
        if action == "tts":
            return {"status": "success", "audio_url": "https://example.com/audio.mp3"}
        else:
            return {"status": "success", "text": "[Transcribed text]"}
