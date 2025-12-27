"""
StockSense Agents Package

Phase 3: The Adversarial Collaboration Update

This package contains specialized AI agents that work together through
structured debate to produce more accurate and balanced investment analysis.

Agents:
- BullAnalyst: Growth-focused analyst identifying opportunities
- BearAnalyst: Risk-focused analyst identifying threats
- Synthesizer: Impartial judge weighing both perspectives
"""

from .base_agent import AgentToolConfig, BaseAnalystAgent
from .bull_analyst import BullAnalyst, BullCase
from .bear_analyst import BearAnalyst, BearCase
from .synthesizer import Synthesizer, SynthesizedVerdict

__all__ = [
    "AgentToolConfig",
    "BaseAnalystAgent", 
    "BullAnalyst",
    "BullCase",
    "BearAnalyst", 
    "BearCase",
    "Synthesizer",
    "SynthesizedVerdict",
]
