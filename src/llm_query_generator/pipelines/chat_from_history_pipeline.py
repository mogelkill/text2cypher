from typing import Generator

from ..chat_history import ChatHistory, MessageType
from ..llm import LLMAdapter
from .base import Pipeline


def format_history_for_qa(query: str, history: ChatHistory) -> str:
    temp_history = history.clone()
    if temp_history[-1].message_type == MessageType.USER:
        temp_history.remove_message(-1)
    formatted_chat_history = ""
    for message in temp_history:
        if message.process:
            if message.message_type == MessageType.SYSTEM:
                continue
            if message.message_type == MessageType.USER:
                formatted_chat_history += f"User: {message.text}\n"
            else:
                formatted_chat_history += f"Assistant: {message.text}\n"

    return f"""You are an assistant that helps to form nice and human understandable answers.
    The information part contains the current chat history that you must use to answer the user.
    The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
    Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
    If the provided information is empty, say that you don't know the answer.
    Information:
    {formatted_chat_history}

    Question: {query}
    Helpful Answer:"""


class ChatFromHistoryPipeline(Pipeline):
    def __init__(self, llm: LLMAdapter, *, is_internal: bool = False) -> None:
        super().__init__(is_internal=is_internal)
        self.llm = llm

    def forward(self, user_input: str, history: ChatHistory) -> Generator[ChatHistory, None, None]:
        if not self.is_internal:
            history.add_user_message(user_input)
            yield history
        formatted_history = format_history_for_qa(user_input, history)
        history.add_assistant_message("")

        for chunk in self.llm.stream_generate(formatted_history):
            history.append_to_last_message(chunk)
            yield history
