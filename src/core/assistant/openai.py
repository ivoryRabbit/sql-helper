from typing import Union, List, Dict

from openai import OpenAI

from src.core.interface.assistant import Assistant


class OpenAIAssistant(Assistant):
    def __init__(self, api_key: str, model: Union[str, None] = None, config=None):
        if config is None:
            config = {}

        self.client = OpenAI(api_key=api_key)
        self.model = model

        self.temperature: float = config.get("temperature", 0.1)
        self.max_tokens: int = config.get("max_tokens", 1000)

    def generate_system_message(self, message: str) -> Dict[str, str]:
        return {"role": "system", "content": message}

    def generate_user_message(self, message: str) -> Dict[str, str]:
        return {"role": "user", "content": message}

    def generate_assistant_message(self, message: str) -> Dict[str, str]:
        return {"role": "assistant", "content": message}

    def submit_prompts(self, prompts: List[Dict[str, str]], **kwargs) -> str:
        if not prompts:
            raise ValueError("Prompt is empty")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=prompts,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content
