from typing import Optional, Any
from app.services.abstract import LLMProvider
from app.core.config import settings
import json
import urllib.request
import urllib.error


class GroqProvider(LLMProvider):
    """cloud-based llm provider using groq api"""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("groq_api_key is required for cloud mode")
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """generates narrative text using groq api"""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                return str(data["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as e:
            raise Exception(f"groq api error: {e.code} - {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            raise Exception(f"network error: {str(e)}")
    
    async def classify_intent(self, user_input: str) -> dict[str, Any]:
        """returns structured json logic using groq api"""
        system_prompt = """you are a game command parser. analyze the user input and return json with:
{
  "action": "move|attack|talk|examine|inventory|unknown",
  "target": "the subject of the action",
  "confidence": 0.0 to 1.0
}"""
        
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 256,
            "response_format": {"type": "json_object"}
        }
        
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                content = str(data["choices"][0]["message"]["content"])
                return json.loads(content)
        except urllib.error.HTTPError as e:
            raise Exception(f"groq api error: {e.code} - {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            raise Exception(f"network error: {str(e)}")
