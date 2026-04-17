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


# ─── Task 3: Skeptic structured output ──────────────────────────────────────

def test_generate_skeptic_uses_structured_output():
    """generate_skeptic_analysis must use with_structured_output, not parse_llm_json."""
    from unittest.mock import MagicMock, patch
    from stocksense.agents.skeptic_agent import generate_skeptic_analysis, SkepticAnalysis, SkepticCritique, BearCase
    from stocksense.core.schemas import SentimentAnalysisResult

    primary = SentimentAnalysisResult(
        overall_sentiment="Bullish",
        overall_confidence=0.7,
        confidence_reasoning="Strong earnings",
        bullish_count=3, bearish_count=1, neutral_count=1, insufficient_data_count=0,
        headline_analyses=[], key_themes=[],
        potential_impact="Moderate Positive",
        risks_identified=[], information_gaps=[],
    )

    expected_result = SkepticAnalysis(
        skeptic_sentiment="Partially Disagree",
        primary_disagreement="China risk ignored",
        critiques=[SkepticCritique(critique="Overconfident", assumption_challenged="Growth", evidence="Slowdown data")],
        bear_cases=[BearCase(argument="Competition", trigger="Market share loss", severity="High")],
        would_change_mind=["Revenue acceleration"],
        hidden_risks=["Regulatory risk"],
        skeptic_confidence=0.65,
    )

    mock_llm = MagicMock()
    structured_chain = MagicMock()
    mock_llm.with_structured_output.return_value = structured_chain
    structured_chain.invoke.return_value = expected_result

    with patch("stocksense.agents.skeptic_agent.get_chat_llm", return_value=mock_llm):
        result = generate_skeptic_analysis(primary, ["Apple beats earnings"], "AAPL")

    mock_llm.with_structured_output.assert_called_once_with(SkepticAnalysis)
    assert result.skeptic_sentiment == "Partially Disagree"
    assert result.skeptic_confidence == 0.65


# ─── Task 4: Analyzer structured output ─────────────────────────────────────

def test_analyze_sentiment_structured_uses_structured_output():
    """analyze_sentiment_structured must call with_structured_output(SentimentAnalysisResult)."""
    from unittest.mock import MagicMock, patch
    from stocksense.core.analyzer import analyze_sentiment_structured
    from stocksense.core.schemas import SentimentAnalysisResult

    expected = SentimentAnalysisResult(
        overall_sentiment="Bullish",
        overall_confidence=0.78,
        confidence_reasoning="3 of 4 headlines positive",
        bullish_count=3, bearish_count=1, neutral_count=0, insufficient_data_count=0,
        headline_analyses=[], key_themes=[],
        potential_impact="Moderate Positive",
        risks_identified=[], information_gaps=[],
    )

    mock_llm = MagicMock()
    structured_chain = MagicMock()
    mock_llm.with_structured_output.return_value = structured_chain
    structured_chain.invoke.return_value = expected

    with patch("stocksense.core.analyzer.get_chat_llm", return_value=mock_llm):
        result = analyze_sentiment_structured(["Apple beats earnings", "iPhone demand strong"])

    mock_llm.with_structured_output.assert_called_once()
    call_args = mock_llm.with_structured_output.call_args[0]
    assert call_args[0].__name__ == "SentimentAnalysisResult"
    assert result.overall_sentiment == "Bullish"
    assert result.overall_confidence == 0.78


def test_analyze_sentiment_structured_empty_headlines_skips_llm():
    """Empty headlines must return early without calling LLM."""
    from unittest.mock import MagicMock, patch
    from stocksense.core.analyzer import analyze_sentiment_structured

    mock_llm = MagicMock()
    with patch("stocksense.core.analyzer.get_chat_llm", return_value=mock_llm):
        result = analyze_sentiment_structured([])

    mock_llm.invoke.assert_not_called()
    assert result.overall_sentiment == "Insufficient Data"


def test_run_streaming_analysis_emits_completed_event_without_fundamentals_keyerror():
    """Streaming analysis should default missing fundamentals to an empty object."""
    import asyncio
    from types import SimpleNamespace
    from stocksense.orchestration.streaming import run_streaming_analysis, StreamEventType

    async def collect_events():
        events = []
        async for event in run_streaming_analysis("AAPL"):
            events.append(event)
        return events

    with patch("stocksense.orchestration.react_flow.fetch_news_headlines", new=SimpleNamespace(invoke=lambda _: {
        "success": True,
        "headlines": ["Apple beats earnings expectations"],
    })), patch("stocksense.orchestration.react_flow.fetch_price_data", new=SimpleNamespace(invoke=lambda _: {
        "success": True,
        "price_data": [],
    })), patch("stocksense.orchestration.react_flow.fetch_fundamentals", new=SimpleNamespace(invoke=lambda _: {
        "success": True,
        "data": {},
    })), patch("stocksense.orchestration.react_flow.analyze_sentiment", new=SimpleNamespace(invoke=lambda _: {
        "success": True,
        "sentiment_report": "Bullish",
        "overall_sentiment": "Bullish",
        "overall_confidence": 0.8,
        "confidence_reasoning": "Positive headline",
        "headline_analyses": [],
        "key_themes": [],
        "potential_impact": "Moderate Positive",
        "risks_identified": [],
        "information_gaps": [],
    })), patch("stocksense.orchestration.react_flow.generate_skeptic_critique", new=SimpleNamespace(invoke=lambda _: {
        "success": True,
        "skeptic_report": "Limited pushback",
        "skeptic_sentiment": "Agree with Reservations",
        "skeptic_confidence": 0.4,
        "primary_disagreement": "",
        "critiques": [],
        "bear_cases": [],
        "hidden_risks": [],
        "would_change_mind": [],
    })):
        events = asyncio.run(collect_events())

    completed_events = [event for event in events if event.event_type == StreamEventType.COMPLETED]
    assert completed_events, "Expected a completed streaming event"
    assert completed_events[-1].data is not None
    assert completed_events[-1].data["fundamental_data"] == {}
