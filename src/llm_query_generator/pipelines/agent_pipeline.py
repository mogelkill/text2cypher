import json
from dataclasses import dataclass
from typing import Generator

from ..chat_history import ChatHistory
from ..db import DataBaseAdapter
from ..llm import LLMAdapter
from .base import Pipeline
from .chat_from_history_pipeline import ChatFromHistoryPipeline
from .chat_pipeline import ChatPipeline
from .qa_pipeline import QAPipeline


@dataclass
class DataBaseDescriptor:
    name: str
    description: str
    adapter: DataBaseAdapter


class AgentPipeline(Pipeline):
    def __init__(
        self,
        json_llm: LLMAdapter,
        chat_llm: LLMAdapter,
        query_llm: LLMAdapter,
        available_dbs: list[DataBaseDescriptor],
        *,
        is_internal: bool = False,
    ) -> None:
        super().__init__(is_internal=is_internal)
        self.json_llm = json_llm
        self.chat_llm = chat_llm
        self.query_llm = query_llm
        self.available_dbs = available_dbs

    def forward(self, user_input: str, history: ChatHistory) -> Generator[ChatHistory, None, None]:
        if not self.is_internal:
            history.add_user_message(user_input)
            yield history

        decision = self.decide(user_input, history)

        if decision["can_answer_from_history"]:
            # Answer from history using normal chat pipeline
            history.add_assistant_message(
                "Ok I will use the current chat history to answer the question 📄.", process=False
            )
            yield history
            chatfromhistory_pipeline = ChatFromHistoryPipeline(self.chat_llm, is_internal=True)
            yield from chatfromhistory_pipeline(user_input, history)

        elif decision["database"] in (db.name for db in self.available_dbs):
            # Answer from database using qa pipeline
            db_descriptor = next(db for db in self.available_dbs if db.name == decision["database"])
            history.add_assistant_message(
                f"Ok I will use the {db_descriptor.name} to answer the question 🔎.", process=False
            )
            yield history
            qa_pipeline = QAPipeline(self.query_llm, self.chat_llm, db_descriptor.adapter, is_internal=True)
            yield from qa_pipeline(user_input, history)
        else:
            history.add_assistant_message(
                "Sry I can`t answer this question with the current chat history or database information 😔."
            )
            yield history

    def generate_decision_prompt(self, question: str, history: ChatHistory) -> str:
        available_db_prompt = ""
        for db in self.available_dbs:
            available_db_prompt += f"{db.name}: {db.description}\n"

        available_db_list = [f'"{db.name}"' for db in self.available_dbs]
        available_db_list.append('"None"')
        available_db_list = ", ".join(available_db_list)

        return f"""Decide if you can answer the question only with the information of the chat history and if not which Database should be used to answer the question.
Important: You must answer in JSON format!
You have the follwing Databases available:
{available_db_prompt}
The question is:{question}
The current chat history is:
{history.format_for_model()}
Follow this example for the output:
{{
  database: Literal[{available_db_list}],
  can_answer_from_history: bool,
}}"""

    def decide(self, user_input: str, history: ChatHistory) -> dict:
        decision_prompt = self.generate_decision_prompt(user_input, history)
        serialized_decision = self.json_llm.generate(decision_prompt)
        decision = json.loads(serialized_decision)
        return decision
