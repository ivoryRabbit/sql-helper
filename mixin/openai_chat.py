from abc import ABC
from typing import Union

from openai import OpenAI
from vanna.base import VannaBase


class OpenAIChat(VannaBase, ABC):
    def __init__(self, api_key: str, model_name: Union[str, None] = None, config=None):
        VannaBase.__init__(self, config=config)
        if config is None:
            config = {}

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

        self.temperature: float = config.get("temperature", 0.7)
        self.max_tokens: int = config.get("max_tokens", 500)

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        if self.model_name is not None:
            model = self.model_name
        else:
            if num_tokens > 3500:
                model = "gpt-3.5-turbo-16k"
            else:
                model = "gpt-3.5-turbo"

        print(
            f"Using model {model} for {num_tokens} tokens (approx)"
        )
        response = self.client.chat.completions.create(
            model=model,
            messages=prompt,
            max_tokens=self.max_tokens,
            stop=None,
            temperature=self.temperature,
        )

        # Find the first response from the chatbot that has text in it (some responses may not have text)
        for choice in response.choices:
            if "text" in choice:
                return choice.text

        # If no response with text is found, return the first response's content (which may be empty)
        return response.choices[0].message.content
