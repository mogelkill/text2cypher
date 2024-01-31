import os

from src.llm_query_generator.chat_history import ChatHistory
from src.llm_query_generator.llm import LLMAdapter, OpenAILLM

API_KEY = os.environ.get("OPENAI_KEY")


def test_adapter_can_be_constructed():
    adapter = OpenAILLM(API_KEY)
    assert adapter is not None
    assert isinstance(adapter, LLMAdapter)


def test_adapter_can_generate():
    adapter = OpenAILLM(API_KEY)
    question = "Hello how are you?"
    answer = adapter.generate(question)
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_adapter_can_chat():
    chat_history = ChatHistory()
    chat_history.add_user_message("Hello how are you?")
    adapter = OpenAILLM(API_KEY)
    answer = adapter.chat(chat_history.format_for_model())
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_adapter_can_continue_conversation():
    chat_history = ChatHistory()
    chat_history.add_user_message("Hello how are you?")
    adapter = OpenAILLM(API_KEY)
    answer = adapter.continue_conversation(chat_history)
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_adapter_can_stream_chat():
    chat_history = ChatHistory()
    chat_history.add_user_message("Hello how are you?")
    adapter = OpenAILLM(API_KEY)
    answer = adapter.stream_chat(chat_history.format_for_model())
    whole_answer = ""
    for chunk in answer:
        whole_answer += chunk
        assert chunk is not None
        assert isinstance(chunk, str)
    assert len(whole_answer) > 0
