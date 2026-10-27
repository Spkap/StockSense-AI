"""Offline regression checks for the Fireworks provider migration."""
import pytest
from stocksense.core import config


@pytest.mark.parametrize('key', ['', 'your_fireworks_key_here', '   '])
def test_missing_or_placeholder_key_is_rejected(monkeypatch, key):
    monkeypatch.setenv('FIREWORKS_API_KEY', key)
    with pytest.raises(config.ConfigurationError, match='FIREWORKS_API_KEY'):
        config.get_chat_llm()


def test_factory_uses_env_model_and_fireworks_token_limit(monkeypatch):
    monkeypatch.setenv('FIREWORKS_API_KEY', 'test-key')
    monkeypatch.setenv('FIREWORKS_MODEL', 'accounts/fireworks/models/test-model')
    captured = {}
    def fake_model(**kwargs):
        captured.update(kwargs)
        return object()
    monkeypatch.setattr(config, 'ChatFireworks', fake_model)
    config.get_chat_llm(temperature=0.2, max_output_tokens=4096)
    assert captured['model'] == 'accounts/fireworks/models/test-model'
    assert captured['max_tokens'] == 4096
    assert captured['fireworks_api_key'] == 'test-key'
    assert 'google_api_key' not in captured


def test_explicit_model_overrides_environment(monkeypatch):
    monkeypatch.setenv('FIREWORKS_API_KEY', 'test-key')
    monkeypatch.setenv('FIREWORKS_MODEL', 'environment-model')
    monkeypatch.setattr(config, 'ChatFireworks', lambda **kwargs: kwargs)
    assert config.get_chat_llm(model='explicit-model')['model'] == 'explicit-model'


def test_missing_integration_dependency_has_actionable_error(monkeypatch):
    monkeypatch.setattr(config, 'ChatFireworks', None)
    with pytest.raises(config.ConfigurationError, match='langchain-fireworks'):
        config.get_chat_llm()
