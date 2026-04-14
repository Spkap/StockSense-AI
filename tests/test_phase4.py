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
