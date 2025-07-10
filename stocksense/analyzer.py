"""
AI-powered sentiment analysis module for StockSense Agent.

This module provides functions to analyze the sentiment of news headlines
using Google's Gemini LLM via the LangChain integration.
"""

import os
from typing import List
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()


def analyze_sentiment_of_headlines(headlines: List[str]) -> str:
    """
    Analyze the sentiment of news headlines using Google's Gemini LLM.
    
    Args:
        headlines (List[str]): List of news headline strings to analyze
    
    Returns:
        str: Formatted sentiment analysis results from the LLM
    """
    try:
        # Validate input
        if not headlines:
            return "No headlines provided for analysis."
        
        # Get Google API key from environment variables
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Error: GOOGLE_API_KEY not found in environment variables")
            return "Error: Google API key not configured."
        
        print(f"Analyzing sentiment for {len(headlines)} headlines using Gemini...")
        
        # Initialize the Google Generative AI model
        llm = GoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3,  # Lower temperature for more consistent sentiment analysis
            max_output_tokens=2048
        )
        
        # Create a numbered list of headlines for the prompt
        numbered_headlines = "\n".join([f"{i+1}. {headline}" for i, headline in enumerate(headlines)])
        
        # Create the sentiment analysis prompt
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
        
        # Invoke the model with the prompt
        response = llm.invoke(prompt)
        
        print("Sentiment analysis completed successfully!")
        return response
        
    except Exception as e:
        error_msg = f"Error during sentiment analysis: {str(e)}"
        print(error_msg)
        return error_msg


if __name__ == '__main__':
    """
    Test the sentiment analysis function with sample headlines.
    """
    print("=" * 70)
    print("Testing StockSense AI Sentiment Analyzer")
    print("=" * 70)
    
    # Sample headlines for testing - mix of positive, negative, and neutral
    sample_headlines = [
        "Apple Reports Record Q4 Earnings, Beats Wall Street Expectations",
        "Apple Stock Falls 3% After iPhone Sales Disappoint Analysts",
        "Apple Announces New AI Features for iPhone and iPad",
        "Regulatory Concerns Mount Over Apple's App Store Policies"
    ]
    
    print("Sample headlines for analysis:")
    for i, headline in enumerate(sample_headlines, 1):
        print(f"{i}. {headline}")
    

    print("\nRunning sentiment analysis...")

    
    # Perform sentiment analysis
    result = analyze_sentiment_of_headlines(sample_headlines)
    
    print("\nSentiment Analysis Results:")
    print("=" * 50)
    print("\n",result)
    

    print("\nTesting completed!")
