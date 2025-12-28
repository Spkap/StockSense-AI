"""
Structured output schemas for StockSense analysis.

These Pydantic models define the expected shape of LLM outputs,
enabling reliable parsing and honest uncertainty quantification.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class HeadlineSentiment(BaseModel):
    """Sentiment analysis for a single headline."""
    
    headline: str = Field(description="The original headline text")
    sentiment: Literal["Bullish", "Bearish", "Neutral", "Insufficient Data"] = Field(
        description="Sentiment classification. Use 'Insufficient Data' when headline is ambiguous or lacks context."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this classification (0.0 = no confidence, 1.0 = certain). Be honest about uncertainty."
    )
    reasoning: str = Field(
        description="Brief explanation (1-2 sentences) of why this sentiment was assigned"
    )
    key_entities: List[str] = Field(
        default_factory=list,
        description="Companies, people, or concepts mentioned that influenced the sentiment"
    )


class KeyTheme(BaseModel):
    """A recurring theme identified across headlines."""
    
    theme: str = Field(description="Name of the theme (e.g., 'Earnings Concerns', 'AI Expansion')")
    sentiment_direction: Literal["Bullish", "Bearish", "Mixed", "Neutral"] = Field(
        description="Overall sentiment direction of this theme"
    )
    headline_count: int = Field(
        ge=1,
        description="Number of headlines contributing to this theme"
    )
    summary: str = Field(
        description="Brief explanation of the theme and its market implications"
    )


class SentimentAnalysisResult(BaseModel):
    """Complete structured sentiment analysis output."""
    
    # Overall assessment
    overall_sentiment: Literal["Bullish", "Bearish", "Neutral", "Insufficient Data"] = Field(
        description="Aggregate sentiment across all headlines. Use 'Insufficient Data' if evidence is too weak or conflicting."
    )
    overall_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the overall assessment. Lower confidence for mixed signals or limited data."
    )
    
    # Confidence explanation
    confidence_reasoning: str = Field(
        description="Explain what factors influenced the confidence level. Be explicit about limitations."
    )
    
    # Quantified breakdown
    bullish_count: int = Field(ge=0, description="Number of headlines classified as Bullish")
    bearish_count: int = Field(ge=0, description="Number of headlines classified as Bearish")
    neutral_count: int = Field(ge=0, description="Number of headlines classified as Neutral")
    insufficient_data_count: int = Field(ge=0, description="Headlines that couldn't be reliably classified")
    
    # Per-headline analysis
    headline_analyses: List[HeadlineSentiment] = Field(
        description="Individual sentiment analysis for each headline"
    )
    
    # Thematic analysis
    key_themes: List[KeyTheme] = Field(
        default_factory=list,
        description="Major themes identified across the headlines (2-4 themes typically)"
    )
    
    # Market implications
    potential_impact: Literal["Strong Positive", "Moderate Positive", "Minimal", "Moderate Negative", "Strong Negative", "Uncertain"] = Field(
        description="Expected impact on stock price. Use 'Uncertain' when signals conflict."
    )
    
    # Risk factors
    risks_identified: List[str] = Field(
        default_factory=list,
        description="Key risks or concerns mentioned in the headlines"
    )
    
    # What we don't know
    information_gaps: List[str] = Field(
        default_factory=list,
        description="Important information that would improve this analysis but is not available"
    )


class DataSource(BaseModel):
    """Metadata about a data source used in analysis."""
    
    source_type: Literal["news_api", "yahoo_finance", "llm_analysis"] = Field(
        description="Type of data source"
    )
    source_name: str = Field(description="Human-readable name (e.g., 'NewsAPI', 'Yahoo Finance')")
    data_freshness: str = Field(description="How recent the data is (e.g., '7 days', 'real-time')")
    reliability_tier: Literal["high", "medium", "low"] = Field(
        description="Reliability of this source. 'high' = official filings, 'medium' = news, 'low' = social"
    )


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process."""
    
    ticker: str = Field(description="Stock ticker analyzed")
    analysis_timestamp: str = Field(description="ISO timestamp of when analysis was performed")
    data_sources: List[DataSource] = Field(
        description="All data sources used in this analysis"
    )
    headlines_analyzed: int = Field(ge=0, description="Total headlines processed")
    price_data_points: int = Field(ge=0, description="Number of price data points used")
    
    # Limitations
    known_limitations: List[str] = Field(
        default_factory=list,
        description="Known limitations of this analysis (data gaps, API limits, etc.)"
    )


class StructuredAnalysisResponse(BaseModel):
    """Complete analysis response with full attribution and uncertainty."""
    
    metadata: AnalysisMetadata = Field(description="Analysis metadata and data sources")
    sentiment: SentimentAnalysisResult = Field(description="Structured sentiment analysis")
    
    # Executive summary (for display)
    executive_summary: str = Field(
        description="2-3 sentence summary suitable for quick reading"
    )
    
    # Explicit uncertainty statement
    uncertainty_statement: str = Field(
        description="Honest statement about what this analysis cannot tell you"
    )
