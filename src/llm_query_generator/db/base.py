from abc import ABC, abstractmethod
from typing import Any

from src.llm_query_generator.chat_history import ChatHistory


class DataBaseAdapter(ABC):
    is_connected: bool = False

    @abstractmethod
    def execute(self, query: str) -> list[dict[str, Any]]:
        """Execute a query and return the result as a string"""
        ...

    @abstractmethod
    def build_prompt(self, question: str) -> str:
        """Build a prompt for the given question"""
        ...

    def build_error_prompt(self, question: str, error_message: str, query: str) -> str:
        """Build a prompt for the given error message"""
        ...

    @abstractmethod
    def connect(self) -> "DataBaseAdapter":
        """Connect to the database"""
        ...

    @abstractmethod
    def disconnect(self) -> "DataBaseAdapter":
        """Disconnect from the database"""
        ...
