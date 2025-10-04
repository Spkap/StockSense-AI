import os
import sys
from typing import List, Dict

# Add the parent directories to Python path to find core module
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_dir = os.path.dirname(current_dir)
stocksense_dir = os.path.dirname(ai_dir)
sys.path.append(stocksense_dir)

from core.config import get_chat_llm, ConfigurationError
from data.collectors.data_collectors import get_news


def analyze_sentiment_of_headlines(news: List[Dict]) -> str:
    """Analyze sentiment of news headlines using Gemini LLM."""
    try:
        if not news:
            return "No headlines provided for analysis."

        llm = get_chat_llm(
            model="gemini-2.5-flash",
            temperature=0.3,
            max_output_tokens=2048
        )
        
        headlines = "\n".join([f"{i+1}. {item['headline']}" for i, item in enumerate(news) if 'headline' in item])
        

        prompt = f"""
You are a financial sentiment analysis expert. Please analyze the sentiment of the following news headlines and provide insights for stock market research.

Headlines to analyze:
{headlines}

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
        raise f"Configuration error: {str(e)}"

    except Exception as e:
        raise f"Error during sentiment analysis: {str(e)}"


if __name__ == "__main__":
    sample_ticker = "AAPL"
    news_data = get_news(sample_ticker, days=7)
    print("Fetched News Headlines:\n", news_data)
    sentiment_report = analyze_sentiment_of_headlines(news_data)
    print(f"Sentiment Analysis Report for {sample_ticker}:\n", sentiment_report)