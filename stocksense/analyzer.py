import os
from typing import List
from .config import get_llm, ConfigurationError


def analyze_sentiment_of_headlines(headlines: List[str]) -> str:
    """Analyze sentiment of news headlines using Gemini LLM."""
    try:
        if not headlines:
            return "No headlines provided for analysis."

        llm = get_llm(
            model="gemini-2.0-flash-lite",
            temperature=0.3,
            max_output_tokens=2048
        )

        numbered_headlines = "\n".join([f"{i+1}. {headline}" for i, headline in enumerate(headlines)])

        prompt = f"""
You are a financial sentiment analysis expert. Please analyze the sentiment of the following news headlines and provide insights for stock market research.

Headlines to analyze:
{numbered_headlines}

For each headline, please:
1. Classify the sentiment as 'Positive', 'Neutral', or 'Negative'
2. Provide a brief justification (1-2 sentences)

Then provide:
- Overall market sentiment summary
- Key themes or concerns identified
- Potential impact on stock price (bullish/bearish/neutral)

Format your response clearly with numbered items corresponding to the headlines, followed by your overall analysis.
"""

        response = llm.invoke(prompt)
        return response

    except ConfigurationError as e:
        error_msg = f"Configuration error: {str(e)}"
        return error_msg

    except Exception as e:
        error_msg = f"Error during sentiment analysis: {str(e)}"
        return error_msg


if __name__ == '__main__':
    sample_headlines = [
        "Apple Reports Record Q4 Earnings, Beats Wall Street Expectations",
        "Apple Stock Falls 3% After iPhone Sales Disappoint Analysts",
        "Apple Announces New AI Features for iPhone and iPad",
        "Regulatory Concerns Mount Over Apple's App Store Policies"
    ]

    result = analyze_sentiment_of_headlines(sample_headlines)