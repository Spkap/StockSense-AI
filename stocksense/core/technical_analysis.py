"""
Technical analysis signal computation from OHLCV price data.

Computes SMA20, SMA50, RSI14, and 30-day annualized volatility.
Used to inject price-derived signals into Bull/Bear agent prompts.

Input: list of dicts with at least a "close" key (and optionally "date").
Output: dict of human-readable signal values.
"""
import math
from typing import Any


def compute_technical_signals(price_data: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute technical analysis signals from OHLCV price history.

    Args:
        price_data: List of dicts, each with at least {"close": float}.
                    Ordered oldest → newest.

    Returns:
        Dict with keys: trend, sma20, sma50, rsi, rsi_signal,
        annualized_volatility, price_vs_sma20_pct.
        Returns {"trend": "insufficient_data"} for fewer than 51 data points.
    """
    if len(price_data) < 51:
        return {"trend": "insufficient_data"}

    closes = [float(p["close"]) for p in price_data]

    # SMA20 and SMA50 (last N closes)
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50

    trend = "uptrend" if sma20 > sma50 else "downtrend"

    # RSI14
    rsi = _compute_rsi(closes, period=14)
    if rsi >= 70:
        rsi_signal = "overbought"
    elif rsi <= 30:
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    # 30-day annualized volatility
    recent_closes = closes[-31:] if len(closes) >= 31 else closes
    returns = [
        (recent_closes[i] - recent_closes[i - 1]) / recent_closes[i - 1]
        for i in range(1, len(recent_closes))
    ]
    if returns:
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        annualized_vol = round(std_dev * math.sqrt(252), 4)
    else:
        annualized_vol = 0.0

    latest_price = closes[-1]
    price_vs_sma20_pct = round((latest_price / sma20 - 1) * 100, 2)

    return {
        "trend": trend,
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "rsi": round(rsi, 1),
        "rsi_signal": rsi_signal,
        "annualized_volatility": annualized_vol,
        "price_vs_sma20_pct": price_vs_sma20_pct,
        "latest_price": round(latest_price, 2),
    }


def _compute_rsi(closes: list[float], period: int = 14) -> float:
    """Wilder's RSI. Requires at least period+1 data points."""
    if len(closes) < period + 1:
        return 50.0  # neutral fallback

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    # Initial averages (simple mean over first period)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder smoothing for remaining values
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def format_technical_signals(signals: dict[str, Any]) -> str:
    """
    Format technical signals as a human-readable block for LLM prompts.

    Returns a string suitable for injection into agent system prompts.
    """
    if signals.get("trend") == "insufficient_data":
        return "TECHNICAL SIGNALS: Insufficient price history for technical analysis."

    vol_pct = round(signals["annualized_volatility"] * 100, 1)
    direction = "above" if signals["price_vs_sma20_pct"] >= 0 else "below"
    abs_pct = abs(signals["price_vs_sma20_pct"])

    return f"""TECHNICAL SIGNALS:
- Trend: {signals['trend'].upper()} (SMA20={signals['sma20']} vs SMA50={signals['sma50']})
- RSI(14): {signals['rsi']} → {signals['rsi_signal'].upper()}
- Price vs SMA20: {abs_pct}% {direction} 20-day moving average
- 30-day Annualized Volatility: {vol_pct}%
- Latest Close: {signals['latest_price']}"""
