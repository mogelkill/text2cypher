from abc import ABC, abstractmethod
from typing import Any, Generator

from ..chat_history import ChatHistory


class Pipeline(ABC):
    def __init__(self, *, is_internal: bool = False) -> None:
        self.is_internal = is_internal

    @abstractmethod
    def forward(self, user_input: str, history: ChatHistory) -> Generator[ChatHistory, None, None]:
        ...

    def __call__(self, user_input: str, history: ChatHistory) -> Generator[ChatHistory, None, None]:
        return self.forward(user_input, history)
