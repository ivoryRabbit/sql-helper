import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

LLMMessage = dict[str, str]  # {"role": "system"|"user"|"assistant", "content": str}


class LLMClient:
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> tuple[str, int]:
        logger.info("LLM generate: model=%s messages=%d", self._model, len(messages))
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        content = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        logger.info("LLM generate done: tokens=%d", tokens)
        return content, tokens

    async def stream_generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        logger.info("LLM stream_generate: model=%s messages=%d", self._model, len(messages))
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
        except Exception as exc:
            logger.error("LLM stream_generate failed to start: %s", exc, exc_info=True)
            raise
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
        logger.debug("LLM stream_generate finished")
