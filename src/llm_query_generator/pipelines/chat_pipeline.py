from typing import Generator

from ..chat_history import ChatHistory
from ..llm import LLMAdapter
from .base import Pipeline


class ChatPipeline(Pipeline):
    def __init__(self, llm: LLMAdapter, *, is_internal: bool = False) -> None:
        super().__init__(is_internal=is_internal)
        self.llm = llm

    def forward(self, user_input: str, history: ChatHistory) -> Generator[ChatHistory, None, None]:
        if not self.is_internal:
            history.add_user_message(user_input)
            yield history
        history.add_assistant_message("")
        for chunk in self.llm.stream_chat(history.format_for_model()):
            history.append_to_last_message(chunk)
            yield history
