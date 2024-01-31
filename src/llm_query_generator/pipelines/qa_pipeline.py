import json
import re
from typing import Any, Generator

from ..chat_history import ChatHistory
from ..db import DataBaseAdapter
from ..llm import LLMAdapter
from .base import Pipeline

MARKDOWN_PATTERN = r"```.*?\n(.*?)```"
GLOBAL_MAX_RETRIES = 10


def execute_query_with_retries(
    db_adapter: DataBaseAdapter,
    query: str,
    history: ChatHistory,
    query_llm: LLMAdapter,
    user_input: str,
    max_retries: int = 2,
) -> Generator[tuple[ChatHistory, list[dict[str, Any]]], None, None]:
    counter = 0
    while True:
        if counter > max_retries or counter > GLOBAL_MAX_RETRIES:
            history.add_assistant_message(
                "Sorry I was not able to generate a valid query. Please try to rephrase your question.", process=False
            )
            yield history, None
            break
        try:
            db_result = db_adapter.execute(query)
            yield history, db_result
            break
        except Exception as e:
            error_message = str(e)
            fixing_prompt = db_adapter.build_error_prompt(user_input, error_message, query)
            query = clean_generation(query_llm.generate(fixing_prompt))
            history.add_assistant_message(
                f"⚠️There was an error with my generated query: I changed it to ```{query}```", process=False
            )
            yield history, None
        finally:
            counter += 1


def clean_generation(query: str) -> str:
    match = re.search(MARKDOWN_PATTERN, query, re.DOTALL)
    if match:
        code = match.group(1)
        return code
    return query


def format_result_for_qa(query: str, result: list[dict[str, Any]]) -> str:
    result = json.dumps(result, indent=4)
    return f"""You are an assistant that helps to form nice and human understandable answers.
    The information part contains the provided information that you must use to construct an answer.
    The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
    Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
    If the provided information is empty, say that you don't know the answer.
    Information:
    {result}

    Question: {query}
    Helpful Answer:"""


class QAPipeline(Pipeline):
    def __init__(
        self,
        query_llm: LLMAdapter,
        chat_llm: LLMAdapter,
        db_adapter: DataBaseAdapter,
        max_retries: int = 2,
        *,
        is_internal: bool = False,
    ) -> None:
        super().__init__(is_internal=is_internal)
        self.query_llm = query_llm
        self.chat_llm = chat_llm
        self.db_adapter = db_adapter
        self.max_retries = max_retries

    def forward(self, user_input: str, history: ChatHistory) -> Generator[ChatHistory, None, None]:
        working_history = history.clone()
        if not self.is_internal:
            history.add_user_message(user_input)
            yield history

        query_prompt = self.db_adapter.build_prompt(user_input)
        cleaned_query = clean_generation(self.query_llm.generate(query_prompt))
        history.add_assistant_message(f"I generated this query for you:\n {cleaned_query}", process=False)
        yield history

        for new_history, db_result in execute_query_with_retries(
            self.db_adapter, cleaned_query, history, self.query_llm, user_input, self.max_retries
        ):
            if new_history is not None:
                history = new_history
            if db_result is not None:
                break
            else:
                yield history

        if db_result is None:
            return

        history.add_assistant_message(
            f"""I found {len(db_result)} database entries!
<details>
<summary>Details</summary>
<br>
<code>
{json.dumps(db_result,indent=4)}
</code>
</details>""",
            process=False,
        )
        yield history

        working_history.add_user_message(format_result_for_qa(user_input, db_result))

        history.add_assistant_message("")
        for chunk in self.chat_llm.stream_chat(working_history.format_for_model()):
            history.append_to_last_message(chunk)
            yield history
