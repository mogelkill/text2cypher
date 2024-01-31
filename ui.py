import logging
import os
import time
from logging import info
from typing import List, Tuple

import gradio as gr

from src.llm_query_generator.chat_history import ChatHistory
from src.llm_query_generator.db import Neo4jAdapter
from src.llm_query_generator.llm import OpenAILLM
from src.llm_query_generator.pipelines import AgentPipeline, DataBaseDescriptor

SYSTEM_PROMPT = "You are a helpfull chat assistant that helps the user answer questions."

FEW_SHOT_EXAMPLES_CLEVR = """
Question: How many stations are between Snoiarty St and Groitz Lane?
Cypher: MATCH path = shortestPath((start:STATION {name: 'Snoiarty St'})-[:EDGE*..50]-(end:STATION {name: 'Groitz Lane'}))
RETURN LENGTH(path) - 1 AS stationsBetween

Question: How many lines is the station Spriaords Palace on?
Cypher: MATCH (:STATION {name: "Spriaords Palace"})-[r:EDGE]-()
RETURN COUNT(DISTINCT r.line_id) AS NumberOfLines

Question: How many music styles does Orange Screic pass through?
Cypher: MATCH (s1:STATION)-[e:EDGE]->(s2:STATION) WHERE e.line_name = 'Orange Screic' UNWIND [s1.music, s2.music] AS musicStyle
RETURN COUNT(DISTINCT musicStyle)

Question: Can you get rail connections at Mclaewn Upon Thames?
Cypher: MATCH (s1:STATION {name: "Mclaewn Upon Thames"})-[:EDGE]->(s2:STATION)
RETURN s1.name AS Station, s2.name AS ConnectedStation, s1.has_rail AS HasRail

"""

CLEVR_DB_ADAPTER = Neo4jAdapter(
    uri=os.getenv("CLEVR_DB_URI", "bolt://localhost:7687"),
    user=os.getenv("CLEVR_DB_USERNAME", ""),
    password=os.getenv("CLEVR_DB_PASSWORD", ""),
    few_shots=FEW_SHOT_EXAMPLES_CLEVR,
)
MOVIE_DB_ADAPTER = Neo4jAdapter(
    uri=os.getenv("MOVIE_DB_URI", "bolt://localhost:7688"),
    user=os.getenv("MOVIE_DB_USERNAME", ""),
    password=os.getenv("MOVIE_DB_PASSWORD", ""),
)
MODEL = os.getenv("OPEN_AI_MODEL", "gpt-4-1106-preview")
CHAT_LLM = OpenAILLM(api_key=os.environ.get("OPENAI_KEY"), model=MODEL, temperature=0.2, max_tokens=200)
QUERY_LLM = OpenAILLM(api_key=os.environ.get("OPENAI_KEY"), model=MODEL, temperature=0.0, max_tokens=100)
JSON_LLM = OpenAILLM(
    api_key=os.environ.get("OPENAI_KEY"),
    model=MODEL,
    temperature=0.0,
    max_tokens=50,
    response_format={"type": "json_object"},
)
DATA_BASE_DESCRIPTORS = [
    DataBaseDescriptor(
        "MovieDatabase", "A neo4j database containing information about movies, actors and directors", MOVIE_DB_ADAPTER
    ),
    DataBaseDescriptor(
        "CLEVR",
        "A neo4j database containing information about underground train stations and underground train lines with their architecture and other addtitional informations",
        CLEVR_DB_ADAPTER,
    ),
]
PIPELINE = AgentPipeline(JSON_LLM, CHAT_LLM, QUERY_LLM, DATA_BASE_DESCRIPTORS)


def chatbot_response(message: str, history: ChatHistory) -> List[Tuple[str, str]]:
    for histroy in PIPELINE(message, history):
        yield histroy.format_for_gradio()


with gr.Blocks(analytics_enabled=False) as demo:
    chat_history = gr.State(ChatHistory().add_system_message(SYSTEM_PROMPT))
    with gr.Accordion("Available Databases"):
        gr.DataFrame(
            headers=["Database Name", "Description"],
            datatype=["str", "str"],
            row_count=len(DATA_BASE_DESCRIPTORS),
            col_count=2,
            value=[[db.name, db.description] for db in DATA_BASE_DESCRIPTORS],
        )
    chatbot = gr.Chatbot()
    input_textbox = gr.Textbox()
    button = gr.Button()

    input_textbox.submit(chatbot_response, inputs=[input_textbox, chat_history], outputs=chatbot).then(
        lambda _: "", input_textbox, input_textbox
    )
    button.click(chatbot_response, inputs=[input_textbox, chat_history], outputs=chatbot).then(
        lambda _: "", input_textbox, input_textbox
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    info("Starting demo server...")
    CLEVR_DB_ADAPTER.connect()
    info("Connected to CLEVR databases...")
    MOVIE_DB_ADAPTER.connect()
    info("Connected to MOVIE databases...")
    demo.queue()
    demo.launch(show_api=False, server_name="0.0.0.0", server_port=7860)
