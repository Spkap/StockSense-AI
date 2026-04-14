"""
Shared utility for robustly parsing JSON from LLM responses.

LLMs return JSON in several formats:
  - Plain: {"key": "value"}
  - Code block: ```json\n{"key": "value"}\n```
  - Code block no tag: ```\n{"key": "value"}\n```
  - Prose + JSON: "Here is the result:\n{"key": "value"}"

All callers should use parse_llm_json() instead of rolling their own split logic.
"""
import json
import re
import logging
from typing import TypeVar, Type, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMParseError(ValueError):
    """Raised when JSON cannot be extracted from an LLM response."""
    pass


def parse_llm_json(content: str, model: Type[T] | None = None) -> Union[dict, list, T]:
    """
    Extract and parse JSON from an LLM response string.

    Handles all common LLM output formats:
    - Plain JSON object or array
    - Fenced code block with ```json ... ``` or ``` ... ```
    - JSON embedded in surrounding prose

    Args:
        content: Raw string from LLM response.
        model: Optional Pydantic model class. If provided, parses into that model.

    Returns:
        dict, list, or Pydantic model instance.

    Raises:
        LLMParseError: If no valid JSON can be found or parsed.
    """
    if not content or not content.strip():
        raise LLMParseError("No JSON found in LLM response: empty content")

    raw = _extract_json_string(content)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise LLMParseError(f"Invalid JSON in LLM response: {e}. Raw: {raw[:200]}") from e

    if model is not None:
        return model(**parsed)
    return parsed


def _extract_json_string(content: str) -> str:
    """Pull the JSON string out of whatever format the LLM used."""
    stripped = content.strip()

    # Try fenced code block first: ```json ... ``` or ``` ... ```
    # Extract whatever is between the fences and let json.loads validate it.
    code_block = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        stripped,
        re.DOTALL,
    )
    if code_block:
        candidate = code_block.group(1).strip()
        # Validate it looks like JSON before returning (must start with { or [)
        if candidate and candidate[0] in ("{", "["):
            return candidate
        # It's in a code block but not parseable JSON — surface as Invalid JSON
        raise LLMParseError(f"Invalid JSON in LLM response (code block): {candidate[:200]}")

    # Try finding first [ to last ] (array) — check BEFORE object
    # so that [{...}] inputs are returned as the full array, not inner {}
    arr_start = stripped.find("[")
    arr_end = stripped.rfind("]")
    obj_start = stripped.find("{")
    obj_end = stripped.rfind("}")

    # Choose whichever valid container starts first
    has_arr = arr_start != -1 and arr_end != -1 and arr_end > arr_start
    has_obj = obj_start != -1 and obj_end != -1 and obj_end > obj_start

    if has_arr and has_obj:
        if arr_start < obj_start:
            return stripped[arr_start : arr_end + 1]
        else:
            return stripped[obj_start : obj_end + 1]
    elif has_arr:
        return stripped[arr_start : arr_end + 1]
    elif has_obj:
        return stripped[obj_start : obj_end + 1]

    raise LLMParseError(
        f"No JSON found in LLM response: {stripped[:200]}"
    )
