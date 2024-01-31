import pytest

from src.llm_query_generator.chat_history import ChatHistory
from src.llm_query_generator.db import DataBaseAdapter, Neo4jAdapter

URI = "bolt://localhost:7688"
USER = ""
PASSWORD = ""


def test_adapter_can_be_constructed():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    assert adapter is not None
    assert isinstance(adapter, DataBaseAdapter)


def test_adapter_can_connect():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    assert adapter.is_connected


def test_adapter_can_disconnect():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    adapter.disconnect()
    assert not adapter.is_connected


def test_adapter_can_execute_query():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    result = adapter.execute("MATCH (n:Movie) RETURN n LIMIT 25")
    assert result is not None
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert "n" in result[0].keys()
    assert len(result) == 25
    adapter.disconnect()


def test_adapter_can_get_schema():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    schema = adapter.get_schema()
    assert schema is not None
    assert isinstance(schema, str)
    adapter.disconnect()


def test_adapter_can_generate_prompt():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    question = "What is the name of the movie?"
    prompt = adapter.build_prompt(question)
    assert prompt is not None
    assert isinstance(prompt, str)
    assert question in prompt
    adapter.disconnect()


pytest.mark.skip(reason="This test is not yet implemented")


def test_adapter_can_generate_decision_prompt():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    question = "What is the name of the movie?"
    history = ChatHistory().add_system_message("Please output valid json")
    history.add_user_message("I want to know the name of the movie")
    available_db = {
        "Neo4j": "This database contains information about movies and actors",
        "MongoDB": "This database contains information sales of books",
        "MySQL": "This database contains information about the weather",
    }
    prompt = adapter.build_decision_prompt(question, history, available_db)
    assert prompt is not None
    assert isinstance(prompt, str)
    assert question in prompt
    for db in available_db.keys():
        assert db in prompt
    for message in history.history:
        assert message.text in prompt
    adapter.disconnect()


pytest.mark.skip(reason="This test is not yet implemented")


def test_adapter_can_generate_answer_on_history_only_prompt():
    adapter = Neo4jAdapter(URI, USER, PASSWORD)
    adapter.connect()
    question = "What is the name of the movie?"
    history = ChatHistory().add_system_message(
        "You are a helpfull chat assistant that helps the user answer questions with information from a chat history."
    )
    history.add_user_message("I want to know the name of the movie")
    prompt = adapter.build_answer_on_history_only_prompt(question, history)
    assert prompt is not None
    assert isinstance(prompt, str)
    assert question in prompt
    for message in history.history:
        assert message.text in prompt
    adapter.disconnect()


def test_adapter_throws_on_infinite_queries():
    adapter = Neo4jAdapter(URI, USER, PASSWORD, query_timeout=1)
    adapter.connect()
    query = "MATCH (n:Person{name:'Keanu Reeves'})-[*]-(other) RETURN count(*) as allPathsCount"
    with pytest.raises(Exception) as e:
        _ = adapter.execute(query)
    assert "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration" in str(e.value)


def test_adapter_throws_on_wrong_syntax_queries():
    adapter = Neo4jAdapter(URI, USER, PASSWORD, query_timeout=1)
    adapter.connect()
    query = "MATCH (n:Person{name:'Keanu Reeves') RETURN n"
    with pytest.raises(Exception) as e:
        _ = adapter.execute(query)
    assert "Neo.ClientError.Statement.SyntaxError" in str(e.value)
