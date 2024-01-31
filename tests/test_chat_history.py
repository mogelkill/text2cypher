from src.llm_query_generator.chat_history import ChatHistory, Message, MessageType


def test_is_constructable():
    chat_history = ChatHistory()
    assert isinstance(chat_history, ChatHistory)


def test_message_can_be_added():
    message = Message("Hello", MessageType.SYSTEM)
    chat_history = ChatHistory()
    chat_history.add(message)
    assert len(chat_history.history) == 1
    assert chat_history.history[0].text == "Hello"
    assert chat_history.history[0].message_type == MessageType.SYSTEM


def test_user_message_can_be_added():
    chat_history = ChatHistory()
    chat_history.add_user_message("Hello")
    assert len(chat_history.history) == 1
    assert chat_history.history[0].text == "Hello"
    assert chat_history.history[0].message_type == MessageType.USER


def test_assistant_message_can_be_added():
    chat_history = ChatHistory()
    chat_history.add_assistant_message("Hello")
    assert len(chat_history.history) == 1
    assert chat_history.history[0].text == "Hello"
    assert chat_history.history[0].message_type == MessageType.ASSISTANT


def test_can_export_to_model_format():
    chat_history = ChatHistory()
    chat_history.add_user_message("ping")
    chat_history.add_assistant_message("pong")
    model_message = chat_history.format_for_model()
    assert len(model_message) == 2
    assert model_message[0]["role"] == "user"
    assert model_message[0]["content"] == "ping"
    assert model_message[1]["role"] == "assistant"
    assert model_message[1]["content"] == "pong"


def test_window_restriction():
    chat_history = ChatHistory(window=2)
    for i in range(5):
        chat_history.add_user_message(str(i))
    model_message = chat_history.format_for_model()
    assert len(model_message) == 2
    assert model_message[0]["content"] == "3"
    assert model_message[1]["content"] == "4"
