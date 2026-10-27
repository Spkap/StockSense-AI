import os
from typing import Optional
from dotenv import load_dotenv

from pathlib import Path

try:
    from langchain_fireworks import ChatFireworks
except ModuleNotFoundError:
    ChatFireworks = None

# Resolve from the repository rather than the caller's working directory.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_MODEL = "accounts/fireworks/models/deepseek-v4p1-flash-1017"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CHAT_TEMPERATURE = 0.1
DEFAULT_CHAT_MAX_TOKENS = 4096


class ConfigurationError(Exception):
    pass


def get_fireworks_api_key() -> str:
    api_key = os.getenv("FIREWORKS_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_"):
        raise ConfigurationError("Set FIREWORKS_API_KEY in the backend .env file.")
    return api_key


def get_chat_llm(model: Optional[str] = None,
                 temperature: float = DEFAULT_CHAT_TEMPERATURE,
                 max_output_tokens: int = DEFAULT_CHAT_MAX_TOKENS):
    """Create the shared Fireworks chat model for all analysis agents."""
    if ChatFireworks is None:
        raise ConfigurationError("Install backend dependencies: langchain-fireworks is missing.")
    selected_model = model or os.getenv("FIREWORKS_MODEL", "").strip() or DEFAULT_MODEL
    return ChatFireworks(
        model=selected_model,
        fireworks_api_key=get_fireworks_api_key(),
        temperature=temperature,
        max_tokens=max_output_tokens,
        max_retries=2,
        request_timeout=90,
    )


def get_llm(model: Optional[str] = None,
            temperature: float = DEFAULT_TEMPERATURE,
            max_output_tokens: int = DEFAULT_MAX_TOKENS):
    """Text-output adapter retained for callers of the legacy LLM factory."""
    from langchain_core.output_parsers import StrOutputParser
    return get_chat_llm(model, temperature, max_output_tokens) | StrOutputParser()


def get_newsapi_key() -> str:
    """Get NewsAPI key from environment variables."""
    api_key = os.getenv('NEWSAPI_KEY')

    if not api_key:
        raise ConfigurationError(
            "NewsAPI key not found. Please set NEWSAPI_KEY environment variable."
        )

    if api_key.strip().startswith("your_"):
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
    get_fireworks_api_key()
    get_newsapi_key()
    return True
