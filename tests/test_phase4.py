"""
Phase 4 tests: tenacity retries, structured output for Synthesizer/Skeptic/Analyzer,
and deterministic mocks for test_tools.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from langchain_core.messages import AIMessage


# ─── Task 1: Tenacity retries ────────────────────────────────────────────────

def test_llm_invoke_retries_on_resource_exhausted():
    """LLM invoke should retry up to 3 times on ResourceExhausted before raising."""
    from google.api_core.exceptions import ResourceExhausted
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = [
        ResourceExhausted("quota exceeded"),
        ResourceExhausted("quota exceeded"),
        AIMessage(content="success"),
    ]

    with patch("stocksense.core.config.get_google_api_key", return_value="fake-key"):
        with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
            llm = get_chat_llm()
            result = llm.invoke("prompt")

    assert result.content == "success"
    assert mock_inner.invoke.call_count == 3


def test_llm_invoke_raises_after_max_retries():
    """LLM invoke should raise after exhausting all 3 retry attempts."""
    from google.api_core.exceptions import ResourceExhausted
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = ResourceExhausted("quota exceeded")

    with patch("stocksense.core.config.get_google_api_key", return_value="fake-key"):
        with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
            llm = get_chat_llm()
            with pytest.raises(ResourceExhausted):
                llm.invoke("prompt")

    assert mock_inner.invoke.call_count == 3


def test_llm_invoke_does_not_retry_on_value_error():
    """Tenacity should NOT retry on non-retriable errors like ValueError."""
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = ValueError("bad input")

    with patch("stocksense.core.config.get_google_api_key", return_value="fake-key"):
        with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
            llm = get_chat_llm()
            with pytest.raises(ValueError):
                llm.invoke("prompt")

    assert mock_inner.invoke.call_count == 1  # no retry


def test_llm_retries_on_service_unavailable():
    """LLM invoke should retry on ServiceUnavailable."""
    from google.api_core.exceptions import ServiceUnavailable
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = [
        ServiceUnavailable("down"),
        AIMessage(content="recovered"),
    ]

    with patch("stocksense.core.config.get_google_api_key", return_value="fake-key"):
        with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
            llm = get_chat_llm()
            result = llm.invoke("prompt")

    assert result.content == "recovered"
    assert mock_inner.invoke.call_count == 2


# ─── Task 2: Synthesizer structured output ───────────────────────────────────

def test_synthesis_llm_output_model_valid():
    from stocksense.agents.synthesizer import SynthesisLLMOutput

    obj = SynthesisLLMOutput(
        bull_probability=0.4,
        base_probability=0.35,
        bear_probability=0.25,
        recommendation="Buy",
        conviction=0.72,
        decisive_factors=["Strong earnings", "AI tailwind"],
        unresolved_questions=["China macro risk"],
        reasoning="Bull case supported by evidence.",
    )
    assert abs(obj.bull_probability + obj.base_probability + obj.bear_probability - 1.0) < 0.01


def test_synthesis_llm_output_rejects_invalid_probability():
    from pydantic import ValidationError
    from stocksense.agents.synthesizer import SynthesisLLMOutput

    with pytest.raises(ValidationError):
        SynthesisLLMOutput(
            bull_probability=1.5,  # > 1.0 — invalid
            base_probability=0.0,
            bear_probability=0.0,
            recommendation="Hold",
            conviction=0.5,
            decisive_factors=[],
            unresolved_questions=[],
            reasoning="test",
        )


def test_generate_synthesis_uses_structured_output():
    """_generate_synthesis must call with_structured_output, not parse_llm_json."""
    import asyncio
    from unittest.mock import MagicMock, patch
    from stocksense.agents.synthesizer import Synthesizer, SynthesisLLMOutput

    mock_llm = MagicMock()
    structured_chain = MagicMock()
    mock_llm.with_structured_output.return_value = structured_chain
    structured_chain.invoke.return_value = SynthesisLLMOutput(
        bull_probability=0.45,
        base_probability=0.35,
        bear_probability=0.20,
        recommendation="Buy",
        conviction=0.7,
        decisive_factors=["Revenue growth"],
        unresolved_questions=[],
        reasoning="Bull case is stronger.",
    )

    s = Synthesizer.__new__(Synthesizer)
    s.llm = mock_llm

    result = asyncio.run(s._generate_synthesis(
        ticker="AAPL",
        bull_case={"thesis": "Growth", "key_claims": [], "confidence": 0.7},
        bear_case={"thesis": "Risk", "key_claims": [], "confidence": 0.4},
        bull_rebuttals=[],
        bear_rebuttals=[],
        evidence_grades=[],
        bull_strength=0.7,
        bear_strength=0.4,
    ))

    mock_llm.with_structured_output.assert_called_once_with(SynthesisLLMOutput)
    assert result["recommendation"] == "Buy"
    assert result["bull_probability"] == 0.45
