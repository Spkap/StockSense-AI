"""
TrackedLLM — transparent LLM wrapper that accumulates token usage.

Usage:
    from stocksense.core.llm_client import TrackedLLM, TokenUsage
    from stocksense.core.config import get_chat_llm

    llm = TrackedLLM(get_chat_llm(), session_id=correlation_id)
    response = llm.invoke(prompt)
    print(llm.usage.total_tokens, llm.usage.estimated_cost_usd)
"""
from __future__ import annotations

from dataclasses import dataclass


# Gemini 2.5 Flash Lite pricing (as of 2026-04-15)
_INPUT_COST_PER_M = 0.075   # USD per 1M input tokens
_OUTPUT_COST_PER_M = 0.300  # USD per 1M output tokens


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def estimated_cost_usd(self) -> float:
        return (
            self.prompt_tokens / 1_000_000 * _INPUT_COST_PER_M
            + self.completion_tokens / 1_000_000 * _OUTPUT_COST_PER_M
        )


class TrackedLLM:
    """
    Wraps any LangChain ChatModel to accumulate UsageMetadata across invocations.

    The wrapped LLM is fully transparent — all kwargs are forwarded verbatim.
    If the underlying response has no usage_metadata (e.g. mock responses in tests),
    the counters stay at zero without raising.
    """

    def __init__(self, llm, session_id: str) -> None:
        self._llm = llm
        self.session_id = session_id
        self.usage = TokenUsage()

    def invoke(self, input, **kwargs):
        response = self._llm.invoke(input, **kwargs)
        meta = getattr(response, "usage_metadata", None)
        if meta is not None:
            self.usage.prompt_tokens += meta.get("input_tokens", 0) if isinstance(meta, dict) else meta.input_tokens
            self.usage.completion_tokens += meta.get("output_tokens", 0) if isinstance(meta, dict) else meta.output_tokens
            self.usage.total_tokens += meta.get("total_tokens", 0) if isinstance(meta, dict) else meta.total_tokens
        return response

    def bind_tools(self, tools, **kwargs):
        """Forward bind_tools so TrackedLLM can be used with tool-binding."""
        return TrackedLLM(self._llm.bind_tools(tools, **kwargs), session_id=self.session_id)

    def with_structured_output(self, schema, **kwargs):
        """Forward with_structured_output so callers can use structured output through TrackedLLM."""
        return self._llm.with_structured_output(schema, **kwargs)
