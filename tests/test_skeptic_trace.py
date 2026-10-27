import json
from types import SimpleNamespace
from unittest.mock import Mock

from stocksense.agents import skeptic_agent
from stocksense.core.schemas import SentimentAnalysisResult


def _primary():
    return SentimentAnalysisResult.model_validate({
        'overall_sentiment': 'Bullish', 'overall_confidence': .7,
        'confidence_reasoning': 'Demand evidence', 'bullish_count': 1,
        'bearish_count': 0, 'neutral_count': 0, 'insufficient_data_count': 0,
        'headline_analyses': [{'headline': 'Demand rose', 'sentiment': 'Bullish',
                               'confidence': .7, 'reasoning': 'Revenue might improve', 'key_entities': []}],
        'key_themes': [{'theme': 'Demand', 'sentiment_direction': 'Bullish',
                        'headline_count': 1, 'summary': 'Demand accelerated'}],
        'potential_impact': 'Moderate Positive', 'risks_identified': ['Supply risk'],
        'information_gaps': ['No margin data'],
    })


def _valid():
    return {'skeptic_sentiment': 'Partially Disagree', 'primary_disagreement': 'Margin is uncertain',
            'critiques': [{'critique': 'Margins unclear', 'assumption_challenged': 'Margins hold',
                           'evidence': 'Margin data missing'}],
            'bear_cases': [{'argument': 'Margins fall', 'trigger': 'Earnings', 'severity': 'Medium'}],
            'skeptic_confidence': .5}


def test_skeptic_prompt_contains_the_primary_reasoning_and_information_gaps(monkeypatch):
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content=json.dumps(_valid()))
    monkeypatch.setattr(skeptic_agent, 'get_chat_llm', lambda **kwargs: llm)
    result = skeptic_agent.generate_skeptic_analysis(_primary(), ['Demand rose'], 'MSFT')
    prompt = llm.bind.return_value.invoke.call_args.args[0]
    assert result.error is None
    assert 'Revenue might improve' in prompt and 'Demand accelerated' in prompt and 'No margin data' in prompt
    assert 'not independently sourced fact-checking' in prompt


def test_skeptic_retries_empty_or_invalid_substance(monkeypatch):
    bad = _valid()
    bad['critiques'][0]['evidence'] = '  '
    bad['bear_cases'][0]['severity'] = 'Extreme'
    llm = Mock()
    llm.bind.return_value.invoke.side_effect = [SimpleNamespace(content=json.dumps(bad)), SimpleNamespace(content=json.dumps(_valid()))]
    monkeypatch.setattr(skeptic_agent, 'get_chat_llm', lambda **kwargs: llm)
    result = skeptic_agent.generate_skeptic_analysis(_primary(), ['Demand rose'], 'MSFT')
    assert result.error is None and llm.bind.return_value.invoke.call_count == 2
