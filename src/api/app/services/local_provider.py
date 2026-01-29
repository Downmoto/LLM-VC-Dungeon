from typing import Optional, Any
from app.services.abstract import LLMProvider
from app.core.config import settings


class LocalProvider(LLMProvider):
    """local llm provider using llama.cpp"""
    
    def __init__(self):
        # placeholder for actual model loading
        self.narrative_model_path = settings.MODEL_PATH_NARRATIVE
        self.logic_model_path = settings.MODEL_PATH_LOGIC
        print(f"initialized local provider with models:")
        print(f"  narrative: {self.narrative_model_path}")
        print(f"  logic: {self.logic_model_path}")
        
        # todo: load actual models here
        # from llama_cpp import Llama
        # self.narrative_model = Llama(model_path=self.narrative_model_path)
        # self.logic_model = Llama(model_path=self.logic_model_path)
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """generates narrative text using local model"""
        # placeholder implementation
        # in production, this would call the actual model
        
        # full_prompt = prompt
        # if system_prompt:
        #     full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # todo: replace with actual model inference
        # output = self.narrative_model(
        #     full_prompt,
        #     max_tokens=1024,
        #     temperature=0.7,
        #     stop=["</s>", "\n\n"]
        # )
        # return output["choices"][0]["text"]
        
        # placeholder response
        return f"[local model would respond to: {prompt[:50]}...]"
    
    async def classify_intent(self, user_input: str) -> dict[str, Any]:
        """returns structured json logic using local model"""
        # placeholder implementation
        # in production, this would use the function-calling model
        
#         system_prompt = """you are a game command parser. analyze the user input and return json with:
# {
#   "action": "move|attack|talk|examine|inventory|unknown",
#   "target": "the subject of the action",
#   "confidence": 0.0 to 1.0
# }"""
        
        # todo: replace with actual model inference
        # output = self.logic_model(
        #     f"{system_prompt}\n\nUser input: {user_input}",
        #     max_tokens=256,
        #     temperature=0.3,
        #     grammar=json_grammar  # would need to define json grammar
        # )
        # return json.loads(output["choices"][0]["text"])
        
        # placeholder response
        return {
            "action": "unknown",
            "target": user_input,
            "confidence": 0.5
        }
