import os

from src.llm_query_generator.chat_history import ChatHistory
from src.llm_query_generator.db import DataBaseAdapter, Neo4jAdapter
from src.llm_query_generator.llm import LLMAdapter, OpenAILLM
from src.llm_query_generator.pipelines.qa_pipeline import execute_query_with_retries

API_KEY = os.environ.get("OPENAI_KEY")

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"


def test_execute_query_with_retries_can_execute_query():
    db_adapter = Neo4jAdapter(URI, USER, PASSWORD).connect()
    history = ChatHistory()
    llm = OpenAILLM(API_KEY, model="gpt-4-1106-preview", temperature=0.0)
    question = "In how many movies did tom hanks play as a actor"
    query = 'MATCH (p:Person {name: "Tom Hanks"})-[:ACTED_IN]->(m:Movie)\nRETURN COUNT(m) AS NumberOfMoviesTomHanksActedIn\n'
    for _, db_answer in execute_query_with_retries(db_adapter, query, history, llm, question):
        assert db_answer is not None
    db_adapter.disconnect()


def test_execute_query_with_retries_can_fix_query():
    db_adapter = Neo4jAdapter(URI, USER, PASSWORD).connect()
    history = ChatHistory()
    llm = OpenAILLM(API_KEY, model="gpt-4-1106-preview", temperature=0.0)
    question = "In how many movies did tom hanks play as a actor"
    query = (
        'MA (p:Person {name: "Tom Hanks"})-[:ACTED_IN]->(m:Movie)\nRETURN COUNT(m) AS NumberOfMoviesTomHanksActedIn\n'
    )

    db_ansers = []
    histories = []
    for output_history, db_answer in execute_query_with_retries(db_adapter, query, history, llm, question):
        db_ansers.append(db_answer)
        histories.append(output_history)

    assert len(db_ansers) == 2
    assert len(histories) == 2
    assert db_ansers[0] is None
    assert db_ansers[1] is not None

    db_adapter.disconnect()
