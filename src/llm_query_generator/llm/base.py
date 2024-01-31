from abc import ABC, abstractmethod
from typing import Generator

from ..chat_history import ChatHistory


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a answer from the given prompt"""
        ...

    @abstractmethod
    def chat(self, formatted_history: list[dict[str, str]]) -> str:
        """Chat with the model"""
        ...

    def continue_conversation(self, history: ChatHistory) -> str:
        """Continue a conversation from given history"""
        formatted_history = history.format_for_model()
        next_message = self.chat(formatted_history)
        return next_message

    @abstractmethod
    def stream_chat(self, formatted_history: list[dict[str, str]]) -> Generator[str, None, None]:
        """Stream a conversation from given history"""
        ...

    @abstractmethod
    def stream_generate(self, prompt: str) -> Generator[str, None, None]:
        """Stream a conversation from given prompt"""
        ...
