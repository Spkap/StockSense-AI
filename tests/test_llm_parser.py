# tests/test_llm_parser.py
import pytest
import json
from stocksense.core.llm_parser import parse_llm_json, LLMParseError


class TestParseLlmJson:
    def test_plain_json_object(self):
        raw = '{"thesis": "bullish", "confidence": 0.8}'
        result = parse_llm_json(raw)
        assert result == {"thesis": "bullish", "confidence": 0.8}

    def test_backtick_json_block(self):
        raw = '```json\n{"thesis": "bullish", "confidence": 0.8}\n```'
        result = parse_llm_json(raw)
        assert result == {"thesis": "bullish", "confidence": 0.8}

    def test_backtick_block_no_language_tag(self):
        raw = '```\n{"thesis": "bullish"}\n```'
        result = parse_llm_json(raw)
        assert result == {"thesis": "bullish"}

    def test_json_with_surrounding_prose(self):
        raw = 'Here is the analysis:\n{"thesis": "bearish"}\nEnd of response.'
        result = parse_llm_json(raw)
        assert result == {"thesis": "bearish"}

    def test_json_array(self):
        raw = '[{"target_claim": "test", "strength": 0.7}]'
        result = parse_llm_json(raw)
        assert result == [{"target_claim": "test", "strength": 0.7}]

    def test_raises_on_no_json(self):
        with pytest.raises(LLMParseError, match="No JSON"):
            parse_llm_json("This response has no JSON at all.")

    def test_raises_on_invalid_json(self):
        with pytest.raises(LLMParseError, match="Invalid JSON"):
            parse_llm_json('```json\n{bad json here\n```')

    def test_pydantic_model_parsing(self):
        from pydantic import BaseModel

        class Simple(BaseModel):
            name: str
            value: float

        raw = '{"name": "test", "value": 1.5}'
        result = parse_llm_json(raw, model=Simple)
        assert isinstance(result, Simple)
        assert result.name == "test"
        assert result.value == 1.5
