import os
from typing import Optional
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
try:
    from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable as GServiceUnavailable
    _GOOGLE_EXCEPTIONS = (ResourceExhausted, GServiceUnavailable)
except ImportError:
    _GOOGLE_EXCEPTIONS = (Exception,)  # type: ignore[assignment]

# Optional import: minimal deployment may not include backend LLM deps
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


def get_llm(model: str = "gemini-2.5-flash-lite",
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


def get_chat_llm(model: str = "gemini-2.5-flash-lite",
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

    _llm = ChatGoogleGenerativeAI(  # type: ignore
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        max_retries=1,
        timeout=30
    )

    class _RetryLLM:
        """Thin proxy that wraps ChatGoogleGenerativeAI with tenacity retry on invoke."""

        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(_GOOGLE_EXCEPTIONS),
            reraise=True,
        )
        def invoke(self, input, **kwargs):
            return self._inner.invoke(input, **kwargs)

    return _RetryLLM(_llm)


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


def get_supabase_url() -> str:
    """Get Supabase URL from environment variables."""
    url = os.getenv('SUPABASE_URL')
    if not url:
        raise ConfigurationError("SUPABASE_URL not found.")
    return url


def get_supabase_key() -> str:
    """Get Supabase Anon Key from environment variables."""
    key = os.getenv('SUPABASE_ANON_KEY')
    if not key:
        raise ConfigurationError("SUPABASE_ANON_KEY not found.")
    return key


def validate_configuration() -> bool:
    """Validate all required configuration is present and valid."""
    get_google_api_key()
    get_newsapi_key()
    return True


DEFAULT_MODEL = "gemini-2.5-flash-lite"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CHAT_TEMPERATURE = 0.1
DEFAULT_CHAT_MAX_TOKENS = 1024