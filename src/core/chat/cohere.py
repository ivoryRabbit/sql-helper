from typing import Union, List, Dict

import cohere

from src.core.interface.chat import Chat


class CohereChat(Chat):
    def __init__(self, api_key: str, model: Union[str, None] = None, config=None):
        if config is None:
            config = {}

        self.client = cohere.Client(api_key=api_key)
        self.model = model

        self.temperature: float = config.get("temperature", 0.2)
        self.max_tokens: int = config.get("max_tokens", 1000)

    def generate_system_message(self, message: str) -> Dict[str, str]:
        return {"role": "SYSTEM", "text": message}

    def generate_user_message(self, message: str) -> Dict[str, str]:
        return {"role": "USER", "text": message}

    def generate_assistant_message(self, message: str) -> Dict[str, str]:
        return {"role": "CHATBOT", "text": message}

    def submit_prompts(self, prompts: List[Dict[str, str]], **kwargs) -> str:
        if not prompts:
            raise Exception("Prompt is empty")

        num_tokens = 0
        for prompt in prompts:
            num_tokens += len(prompt["content"]) / 4

        if self.model is not None:
            model = self.model
        else:
            model = "command-r-plus"

        response = self.client.chat(
            model=model,
            chat_history=prompts[:-1],
            message=prompts[-1]["text"],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.text
