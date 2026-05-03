import abc
import logging
from collections.abc import AsyncIterator

import google.generativeai as genai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

LLMMessage = dict[str, str]  # {"role": "system"|"user"|"assistant", "content": str}


class BaseLLMClient(abc.ABC):
    @property
    @abc.abstractmethod
    def model(self) -> str: ...

    @abc.abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> tuple[str, int]: ...

    @abc.abstractmethod
    def stream_generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> AsyncIterator[str]: ...


class OpenAILLMClient(BaseLLMClient):
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> tuple[str, int]:
        logger.info("OpenAI generate: model=%s messages=%d", self._model, len(messages))
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        content = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        logger.info("OpenAI generate done: tokens=%d", tokens)
        return content, tokens

    async def stream_generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        logger.info("OpenAI stream_generate: model=%s messages=%d", self._model, len(messages))
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
        except Exception as exc:
            logger.error("OpenAI stream_generate failed to start: %s", exc, exc_info=True)
            raise
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
        logger.debug("OpenAI stream_generate finished")


class GeminiLLMClient(BaseLLMClient):
    DEFAULT_MODEL = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        genai.configure(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @staticmethod
    def _convert_messages(
        messages: list[LLMMessage],
    ) -> tuple[str | None, list[dict]]:
        """Split OpenAI-style messages into (system_instruction, gemini_contents)."""
        system_parts: list[str] = []
        contents: list[dict] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_parts.append(content)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})
        system_instruction = "\n\n".join(system_parts) if system_parts else None
        return system_instruction, contents

    def _make_model(self, system_instruction: str | None, temperature: float) -> genai.GenerativeModel:
        kwargs: dict = {"model_name": self._model}
        if system_instruction:
            kwargs["system_instruction"] = system_instruction
        kwargs["generation_config"] = genai.types.GenerationConfig(temperature=temperature)
        return genai.GenerativeModel(**kwargs)

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> tuple[str, int]:
        logger.info("Gemini generate: model=%s messages=%d", self._model, len(messages))
        system_instruction, contents = self._convert_messages(messages)
        gemini_model = self._make_model(system_instruction, temperature)
        resp = await gemini_model.generate_content_async(contents)
        text = resp.text or ""
        tokens = resp.usage_metadata.total_token_count if resp.usage_metadata else 0
        logger.info("Gemini generate done: tokens=%d", tokens)
        return text, tokens

    async def stream_generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        logger.info("Gemini stream_generate: model=%s messages=%d", self._model, len(messages))
        system_instruction, contents = self._convert_messages(messages)
        gemini_model = self._make_model(system_instruction, temperature)
        try:
            stream = await gemini_model.generate_content_async(contents, stream=True)
        except Exception as exc:
            logger.error("Gemini stream_generate failed to start: %s", exc, exc_info=True)
            raise
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
        logger.debug("Gemini stream_generate finished")


# Keep backward-compatible alias
LLMClient = BaseLLMClient


def create_llm_client(provider: str, openai_api_key: str, google_api_key: str, model: str) -> BaseLLMClient:
    if provider == "gemini":
        return GeminiLLMClient(api_key=google_api_key, model=model)
    return OpenAILLMClient(api_key=openai_api_key, model=model)
