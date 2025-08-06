"""
Centralized configuration module for StockSense ReAct Agent.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI

load_dotenv()


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def get_google_api_key() -> str:
    """Get and validate Google API key from environment variables."""
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        raise ConfigurationError(
            "Google API key not found. Please set GOOGLE_API_KEY environment variable."
        )
    
    if api_key == "your_actual_google_api_key_here":
        raise ConfigurationError(
            "Google API key is still set to placeholder value. Please configure with your actual API key."
        )
    
    return api_key


def get_llm(model: str = "gemini-1.5-flash", 
           temperature: float = 0.3, 
           max_output_tokens: int = 2048) -> GoogleGenerativeAI:
    """Get configured Google Generative AI LLM instance."""
    api_key = get_google_api_key()
    
    return GoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens
    )


def get_chat_llm(model: str = "gemini-1.5-flash", 
                temperature: float = 0.1, 
                max_output_tokens: int = 1024) -> ChatGoogleGenerativeAI:
    api_key = get_google_api_key()
    
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        max_retries=3,
        timeout=30,
        requests_per_minute=30
    )


def get_newsapi_key() -> str:
    """Get and validate NewsAPI key from environment variables."""
    api_key = os.getenv('NEWSAPI_KEY')
    
    if not api_key:
        raise ConfigurationError(
            "NewsAPI key not found. Please set NEWSAPI_KEY environment variable."
        )
    
    if api_key == "your_actual_newsapi_key_here":
        raise ConfigurationError(
            "NewsAPI key is still set to placeholder value. Please configure with your actual API key."
        )
    
    return api_key


def validate_configuration() -> bool:
    """Validate all required configuration is present and valid."""
    get_google_api_key()
    get_newsapi_key()
    return True


DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CHAT_TEMPERATURE = 0.1
DEFAULT_CHAT_MAX_TOKENS = 1024
