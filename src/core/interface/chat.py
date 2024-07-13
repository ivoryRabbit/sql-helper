from abc import ABC, abstractmethod
from typing import Any


class Chat(ABC):
    @abstractmethod
    def generate_system_message(self, message: str) -> Any:
        pass

    @abstractmethod
    def generate_assistant_message(self, message: str) -> Any:
        pass

    @abstractmethod
    def generate_user_message(self, message: str) -> Any:
        pass

    @abstractmethod
    def submit_prompts(self, prompts: list, **kwargs) -> str:
        pass

