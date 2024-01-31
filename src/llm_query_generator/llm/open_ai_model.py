from typing import Generator, Optional

from openai import OpenAI

from .base import LLMAdapter


class OpenAILLM(LLMAdapter):
    """ "OpenAI Language Model"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo-1106",
        temperature: float = 0.7,
        max_tokens: int = 50,
        response_format: Optional[dict] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=api_key)
        self.response_format = response_format

    def generate(self, prompt: str) -> str:
        message = [{"role": "user", "content": prompt}]
        return self.chat(message)

    def chat(self, formatted_history: list[dict[str, str]]) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=formatted_history,
            response_format=self.response_format,
        )
        return completion.choices[0].message.content

    def stream_chat(self, formatted_history: list[dict[str, str]]) -> Generator[str, None, None]:
        stream = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=formatted_history,
            response_format=self.response_format,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def stream_generate(self, prompt: str) -> Generator[str, None, None]:
        message = [{"role": "user", "content": prompt}]
        yield from self.stream_chat(message)
