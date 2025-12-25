
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from stocksense.scheduler import check_all_active_theses

@pytest.mark.asyncio
async def test_check_all_active_theses():
    # Mock Supabase Client
    mock_supabase = MagicMock()
    mock_response_theses = MagicMock()
    mock_response_theses.data = [
        {"id": "thesis_1", "user_id": "user_1", "ticker": "AAPL", "kill_criteria": ["bad news"]},
        {"id": "thesis_2", "user_id": "user_2", "ticker": "AAPL", "kill_criteria": ["price drop"]},
        {"id": "thesis_3", "user_id": "user_1", "ticker": "TSLA", "kill_criteria": ["elon tweet"]}
    ]
    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.execute.return_value = mock_response_theses

    # Mock React Analysis
    mock_analysis_result = {
        "summary": "This is a summary. Bad news for AAPL.",
        "sentiment_report": "Bearish",
        "key_themes": [],
        "risks_identified": [],
        "bear_cases": [],
        "hidden_risks": [],
        "overall_sentiment": "Bearish",
        "overall_confidence": 0.9
    }

    # Use patch to mock external calls
    with patch("stocksense.scheduler.get_supabase_client", return_value=mock_supabase), \
         patch("stocksense.scheduler.run_react_analysis", return_value=mock_analysis_result) as mock_run_analysis, \
         patch("stocksense.scheduler.check_kill_criteria_for_ticker") as mock_check_kill: # Mocking this to simplify test, though scheduler logic duplicates some of it

        # Run the function
        await check_all_active_theses()

        # Verify analysis was run for unique tickers
        assert mock_run_analysis.call_count == 2
        mock_run_analysis.assert_any_call("AAPL")
        mock_run_analysis.assert_any_call("TSLA")

        # Verify alerts would be inserted (we are mocking the insert call in the implementation, so let's check table insert calls)
        # In our implementation we call client.table("alert_history").insert(...).execute()
        # AAPL triggered "bad news" from our mock analysis summary?
        # Actually our mock 'check_all_active_theses' implements manual matching logic.
        # We need to mock 'extract_signals_from_analysis' and 'match_signals_to_criteria' to control flow.
        
    # Re-run with deeper mocks for logic verification
    with patch("stocksense.scheduler.get_supabase_client", return_value=mock_supabase), \
         patch("stocksense.scheduler.run_react_analysis", return_value=mock_analysis_result), \
         patch("stocksense.scheduler.extract_signals_from_analysis", return_value=[{"signal": "Bad News"}]), \
         patch("stocksense.scheduler.match_signals_to_criteria") as mock_match:
        
        # Mock a successful match
        mock_match_obj = MagicMock()
        mock_match_obj.match_confidence = 0.8
        mock_match_obj.criteria = "bad news"
        mock_match_obj.signal = "Bad News detected"
        mock_match.return_value = [mock_match_obj]

        await check_all_active_theses()
        
        # Verify insert was called
        assert mock_supabase.table.return_value.insert.call_count >= 3
