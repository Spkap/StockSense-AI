import os
from typing import Optional
from dotenv import load_dotenv

try:
    from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI  # type: ignore
    _GENAI_AVAILABLE = True
except ModuleNotFoundError:
    GoogleGenerativeAI = None  # type: ignore
    ChatGoogleGenerativeAI = None  # type: ignore
    _GENAI_AVAILABLE = False

load_dotenv()


class ConfigurationError(Exception):
    pass


def get_google_api_key() -> str:
    """Get Google API key from environment variables."""
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


def get_llm(model: str = "gemini-2.0-flash-lite",
           temperature: float = 0.3,
           max_output_tokens: int = 2048):  # return type conditional
    """Get configured Google Generative AI LLM instance.

    This function is safe to call even if langchain-google-genai is not installed.
    In that case it raises a ConfigurationError with a clear message instead of
    causing an immediate ModuleNotFoundError during import of this module.
    """
    if not _GENAI_AVAILABLE or GoogleGenerativeAI is None:  # type: ignore
        raise ConfigurationError(
            "langchain-google-genai dependency not installed. Install backend requirements or add 'langchain-google-genai' to requirements.txt for LLM features."
        )

    api_key = get_google_api_key()

    return GoogleGenerativeAI(  # type: ignore
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens
    )


def get_chat_llm(model: str = "gemini-2.0-flash-lite",
                temperature: float = 0.1,
                max_output_tokens: int = 1024):  # return type conditional
    """Get configured Google Generative AI Chat LLM instance.

    Raises ConfigurationError with guidance if dependency missing.
    """
    if not _GENAI_AVAILABLE or ChatGoogleGenerativeAI is None:  # type: ignore
        raise ConfigurationError(
            "langchain-google-genai dependency not installed. Install backend requirements or add 'langchain-google-genai' to requirements.txt for chat LLM features."
        )

    api_key = get_google_api_key()

    return ChatGoogleGenerativeAI(  # type: ignore
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        max_retries=3,
        timeout=30
        # Removed requests_per_minute - deprecated parameter
    )


def get_newsapi_key() -> str:
    """Get NewsAPI key from environment variables."""
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


DEFAULT_MODEL = "gemini-2.0-flash-lite"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CHAT_TEMPERATURE = 0.1
DEFAULT_CHAT_MAX_TOKENS = 1024