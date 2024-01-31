from copy import deepcopy
from dataclasses import dataclass
from enum import Enum


class MessageType(str, Enum):
    """Types of messages in the chat history"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A message in the chat history"""

    text: str
    message_type: MessageType
    display: bool = True
    process: bool = True


class ChatHistory:
    """Keeps the chat history of the whole conversation"""

    def __init__(self, window: int = 10):
        self.history: list[Message] = []
        self.window = window

    def __getitem__(self, index: int) -> Message:
        """Returns a message from the chat history"""
        return self.history[index]

    def __iter__(self):
        yield from self.history[-self.window :]

    def clone(self) -> "ChatHistory":
        """Returns a clone of the chat history"""
        clone = ChatHistory(self.window)
        for message in self.history:
            clone.add(deepcopy(message))
        return clone

    def add(self, message: Message):
        """Adds a message to the chat history"""
        self.history.append(message)

    def add_user_message(self, text: str, *, display: bool = True, process: bool = True) -> "ChatHistory":
        """Adds a user message to the chat history"""
        self.add(Message(text, MessageType.USER, display, process))
        return self

    def add_assistant_message(self, text: str, *, display: bool = True, process: bool = True) -> "ChatHistory":
        """Adds an assistant message to the chat history"""
        self.add(Message(text, MessageType.ASSISTANT, display, process))
        return self

    def add_system_message(self, text: str) -> "ChatHistory":
        """Adds a system message to the chat history"""
        self.add(Message(text, MessageType.SYSTEM))
        return self

    def append_to_last_message(self, text: str) -> "ChatHistory":
        self.history[-1].text += text
        return self

    def remove_message(self, index: int) -> "ChatHistory":
        """Removes a message from the chat history"""
        self.history.pop(index)
        return self

    def format_for_model(self) -> list[dict[str, str]]:
        """Formats the chat history for the model"""
        result = []
        for message in self.history[-self.window :]:
            if message.process is False or message.text == "":
                continue
            result.append({"role": message.message_type.value, "content": message.text})

        return result

    def format_for_gradio(self) -> list[tuple[str, str]]:
        """Return a list of tuples where each tuple contains the (User, Assistant) as messages as markdown"""
        result = []
        for message in self.history:
            if message.display is False:
                continue
            if message.message_type == MessageType.USER:
                result.append((message.text, None))
            elif message.message_type == MessageType.ASSISTANT:
                result.append((None, message.text))
        return result
