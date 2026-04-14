"""
Phase 3 tests: token tracking, audit trail, structured output, Bayesian credibility,
semantic rebuttal matching, prompt versioning, and debate loop wiring.
"""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass


# ─── Task 1: TrackedLLM ─────────────────────────────────────────────────────

def test_tracked_llm_accumulates_usage():
    from stocksense.core.llm_client import TrackedLLM, TokenUsage
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    mock_llm = MagicMock()
    response = AIMessage(
        content='{"hello": "world"}',
        usage_metadata=UsageMetadata(input_tokens=10, output_tokens=20, total_tokens=30),
    )
    mock_llm.invoke.return_value = response

    tracked = TrackedLLM(mock_llm, session_id="test-session")
    result = tracked.invoke("prompt")

    assert result.content == '{"hello": "world"}'
    assert tracked.usage.prompt_tokens == 10
    assert tracked.usage.completion_tokens == 20
    assert tracked.usage.total_tokens == 30


def test_tracked_llm_accumulates_across_calls():
    from stocksense.core.llm_client import TrackedLLM
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    mock_llm = MagicMock()
    response = AIMessage(
        content="x",
        usage_metadata=UsageMetadata(input_tokens=5, output_tokens=5, total_tokens=10),
    )
    mock_llm.invoke.return_value = response

    tracked = TrackedLLM(mock_llm, session_id="s")
    tracked.invoke("a")
    tracked.invoke("b")

    assert tracked.usage.prompt_tokens == 10
    assert tracked.usage.completion_tokens == 10
    assert tracked.usage.total_tokens == 20


def test_tracked_llm_no_usage_metadata_does_not_crash():
    from stocksense.core.llm_client import TrackedLLM
    from langchain_core.messages import AIMessage

    mock_llm = MagicMock()
    response = AIMessage(content="plain response")
    mock_llm.invoke.return_value = response

    tracked = TrackedLLM(mock_llm, session_id="s")
    result = tracked.invoke("prompt")

    assert result.content == "plain response"
    assert tracked.usage.total_tokens == 0


def test_estimated_cost_gemini_flash():
    from stocksense.core.llm_client import TokenUsage
    usage = TokenUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000)
    # input: $0.075/M, output: $0.30/M
    assert abs(usage.estimated_cost_usd - 0.375) < 0.001


# ─── Task 2: TraceLogger ────────────────────────────────────────────────────

def test_trace_logger_builds_row_correctly():
    from stocksense.db.trace_logger import TraceLogger

    with patch("stocksense.db.trace_logger.get_supabase_client") as mock_client:
        mock_table = MagicMock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = MagicMock()

        logger = TraceLogger(run_id="abc123")
        logger.log_step(
            step_name="bull_analyst",
            prompt_snapshot="You are bullish...",
            response_snapshot='{"thesis": "Strong buy"}',
            token_count=500,
            duration_ms=1200,
        )

        mock_client.return_value.table.assert_called_once_with("analysis_traces")
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["run_id"] == "abc123"
        assert call_args["step_name"] == "bull_analyst"
        assert call_args["token_count"] == 500
        assert call_args["duration_ms"] == 1200


def test_trace_logger_silently_ignores_supabase_errors():
    from stocksense.db.trace_logger import TraceLogger

    with patch("stocksense.db.trace_logger.get_supabase_client") as mock_client:
        mock_client.return_value.table.side_effect = Exception("Supabase down")

        logger = TraceLogger(run_id="xyz")
        # Must not raise
        logger.log_step("synthesizer", "prompt", "response", 100, 500)


# ─── Task 3: Prompt Versioning ──────────────────────────────────────────────

def test_get_prompt_returns_known_key():
    from stocksense.core.prompts import get_prompt
    result = get_prompt("bull_system_v1")
    assert "bullish" in result.lower() or "bull" in result.lower()
    assert len(result) > 50


def test_get_prompt_raises_on_unknown_key():
    from stocksense.core.prompts import get_prompt
    with pytest.raises(KeyError):
        get_prompt("nonexistent_prompt_key")


def test_all_prompt_keys_return_non_empty():
    from stocksense.core.prompts import PROMPTS
    for key, value in PROMPTS.items():
        assert isinstance(value, str) and len(value) > 20, f"Prompt '{key}' is too short"


def test_bull_analyst_uses_prompt_registry():
    """BullAnalyst._build_system_prompt must delegate to the prompt registry."""
    from stocksense.agents.bull_analyst import BullAnalyst
    from stocksense.core.prompts import get_prompt
    bull = BullAnalyst()
    result = bull._build_system_prompt()
    assert result == get_prompt("bull_system_v1")


def test_bear_analyst_uses_prompt_registry():
    """BearAnalyst._build_system_prompt must delegate to the prompt registry."""
    from stocksense.agents.bear_analyst import BearAnalyst
    from stocksense.core.prompts import get_prompt
    bear = BearAnalyst()
    result = bear._build_system_prompt()
    assert result == get_prompt("bear_system_v1")


# ─── Task 4: Structured Output ──────────────────────────────────────────────

def test_bull_llm_output_schema_validates():
    from stocksense.agents.bull_analyst import BullLLMOutput, CatalystModel
    from pydantic import ValidationError

    # valid
    obj = BullLLMOutput(
        thesis="Strong growth driven by AI",
        catalysts=[
            CatalystModel(description="AI expansion", timeframe="near-term", probability=0.8, potential_impact="high")
        ],
        key_metrics={"revenue_growth": "8%"},
        upside_reasoning="Services segment growing",
        confidence=0.72,
        weaknesses=["Competition"],
        key_claims=[],
    )
    assert obj.confidence == 0.72

    # invalid — confidence out of range
    with pytest.raises(ValidationError):
        BullLLMOutput(
            thesis="t", catalysts=[], key_metrics={}, upside_reasoning="u",
            confidence=1.5,   # > 1.0 — should fail
            weaknesses=[], key_claims=[],
        )


def test_bear_llm_output_schema_validates():
    from stocksense.agents.bear_analyst import BearLLMOutput, RiskModel

    obj = BearLLMOutput(
        thesis="Declining margins pose risk",
        risks=[RiskModel(description="Margin compression", category="financial", severity="high", probability=0.6, timeframe="near-term")],
        red_flags=["Revenue declining"],
        key_metrics={"debtToEquity": "180"},
        downside_reasoning="Competition intensifying",
        confidence=0.65,
        what_would_make_bullish=["Revenue rebound"],
        key_claims=[],
    )
    assert obj.confidence == 0.65


# ─── Task 5: Bayesian Credibility + Semantic Rebuttal ───────────────────────

def test_bayesian_credibility_strong_evidence_weak_rebuttal():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)  # skip __init__ (needs LLM)
    s.llm = None

    # Strong evidence (0.8), weak rebuttal (0.1) → high posterior
    result = s._calculate_credibility(prior=0.8, rebuttal_strength=0.1)
    assert result > 0.8, f"Expected > 0.8, got {result}"


def test_bayesian_credibility_weak_evidence_strong_rebuttal():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    # Weak evidence (0.3), strong rebuttal (0.9) → low posterior
    result = s._calculate_credibility(prior=0.3, rebuttal_strength=0.9)
    assert result < 0.3, f"Expected < 0.3, got {result}"


def test_bayesian_credibility_clamped_to_unit_interval():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    for prior, rebuttal in [(0.0, 0.0), (1.0, 1.0), (0.5, 0.5)]:
        result = s._calculate_credibility(prior=prior, rebuttal_strength=rebuttal)
        assert 0.0 <= result <= 1.0, f"Out of range for prior={prior}, rebuttal={rebuttal}"


def test_find_matching_rebuttal_semantic_match():
    """Semantic matching should find the relevant rebuttal even without keyword overlap."""
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    claim = {"statement": "Company revenue growth is accelerating"}
    rebuttals = [
        {"target_claim": "Sales are rising quickly", "strength": 0.7},   # semantic match
        {"target_claim": "Management team is weak", "strength": 0.5},    # unrelated
    ]

    with patch("stocksense.agents.synthesizer.GoogleGenerativeAIEmbeddings") as mock_emb_cls:
        mock_emb = MagicMock()
        mock_emb_cls.return_value = mock_emb
        # claim embedding: unit vector [1,0]
        mock_emb.embed_query.return_value = [1.0, 0.0]
        # first rebuttal similar [0.95, 0.31], second dissimilar [0.0, 1.0]
        mock_emb.embed_documents.return_value = [[0.95, 0.31], [0.0, 1.0]]

        result = s._find_matching_rebuttal(claim, rebuttals)
        assert result is not None
        assert result["strength"] == 0.7   # matched the first (similar) rebuttal


def test_find_matching_rebuttal_returns_none_below_threshold():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    claim = {"statement": "Revenue accelerating"}
    rebuttals = [{"target_claim": "Completely unrelated topic", "strength": 0.5}]

    with patch("stocksense.agents.synthesizer.GoogleGenerativeAIEmbeddings") as mock_emb_cls:
        mock_emb = MagicMock()
        mock_emb_cls.return_value = mock_emb
        mock_emb.embed_query.return_value = [1.0, 0.0]
        mock_emb.embed_documents.return_value = [[0.0, 1.0]]  # cosine sim = 0.0

        result = s._find_matching_rebuttal(claim, rebuttals)
        assert result is None


# ─── Task 6: Debate Loop Wiring ─────────────────────────────────────────────

def test_run_debate_analysis_returns_token_usage():
    """run_debate_analysis result dict must contain token_usage key."""
    import asyncio
    from unittest.mock import AsyncMock
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    # Mock the heavy IO so no network calls happen
    dummy_ai = AIMessage(
        content='{"thesis":"t","catalysts":[],"key_metrics":{},"upside_reasoning":"u","confidence":0.6,"weaknesses":[],"key_claims":[]}',
        usage_metadata=UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150),
    )

    with patch("stocksense.orchestration.react_flow.get_fundamental_data", return_value={}), \
         patch("stocksense.orchestration.react_flow.get_news", return_value=["headline"]), \
         patch("stocksense.orchestration.react_flow.get_price_history", return_value=[{"close": 200.0}] * 60), \
         patch("stocksense.orchestration.react_flow.analyze_sentiment_structured") as mock_sent, \
         patch("stocksense.core.config.get_chat_llm") as mock_llm_factory:

        from stocksense.core.schemas import SentimentAnalysisResult
        mock_sent.return_value = SentimentAnalysisResult(
            overall_sentiment="Bullish", overall_confidence=0.7,
            confidence_reasoning="", bullish_count=1, bearish_count=0,
            neutral_count=0, insufficient_data_count=0,
            headline_analyses=[], key_themes=[], potential_impact="Strong Positive",
            risks_identified=[], information_gaps=[],
        )

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = MagicMock(
            thesis="t", catalysts=[], key_metrics={}, upside_reasoning="u",
            confidence=0.6, weaknesses=[], key_claims=[],
            risks=[], red_flags=[], downside_reasoning="d", what_would_make_bullish=[],
        )
        mock_llm.invoke.return_value = dummy_ai
        mock_llm_factory.return_value = mock_llm

        from stocksense.orchestration.react_flow import run_debate_analysis
        result = asyncio.run(run_debate_analysis("AAPL"))

    assert "token_usage" in result, "result must have 'token_usage' key"
    assert isinstance(result["token_usage"], dict)
    assert "total_tokens" in result["token_usage"]


def test_run_debate_analysis_returns_run_id():
    """run_debate_analysis result dict must contain 8-char hex run_id."""
    import asyncio
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    dummy_ai = AIMessage(
        content="{}",
        usage_metadata=UsageMetadata(input_tokens=10, output_tokens=5, total_tokens=15),
    )

    with patch("stocksense.orchestration.react_flow.get_fundamental_data", return_value={}), \
         patch("stocksense.orchestration.react_flow.get_news", return_value=[]), \
         patch("stocksense.orchestration.react_flow.get_price_history", return_value=[{"close": 200.0}] * 60), \
         patch("stocksense.orchestration.react_flow.analyze_sentiment_structured") as mock_sent, \
         patch("stocksense.core.config.get_chat_llm") as mock_llm_factory:

        from stocksense.core.schemas import SentimentAnalysisResult
        mock_sent.return_value = SentimentAnalysisResult(
            overall_sentiment="Neutral", overall_confidence=0.5,
            confidence_reasoning="", bullish_count=0, bearish_count=0,
            neutral_count=0, insufficient_data_count=0,
            headline_analyses=[], key_themes=[], potential_impact="Minimal",
            risks_identified=[], information_gaps=[],
        )

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = MagicMock(
            thesis="t", catalysts=[], key_metrics={}, upside_reasoning="u",
            confidence=0.5, weaknesses=[], key_claims=[],
            risks=[], red_flags=[], downside_reasoning="d", what_would_make_bullish=[],
        )
        mock_llm.invoke.return_value = dummy_ai
        mock_llm_factory.return_value = mock_llm

        from stocksense.orchestration.react_flow import run_debate_analysis
        result = asyncio.run(run_debate_analysis("MSFT"))

    assert "run_id" in result, "result must have 'run_id' key"
    assert len(result["run_id"]) == 8, f"run_id should be 8 chars, got '{result['run_id']}'"
