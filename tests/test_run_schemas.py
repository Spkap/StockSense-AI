import pytest
from pydantic import ValidationError

from stocksense.core.run_schemas import RunRecord, RunStreamEvent


def test_run_stream_event_accepts_valid_event_type():
    event = RunStreamEvent(
        type="source_completed",
        run_id="run_1",
        run_type="research_room",
        ticker="AMD",
        phase="sources",
        progress=0.4,
        message="SEC filings loaded",
    )

    assert event.type == "source_completed"
    assert event.ticker == "AMD"


def test_run_stream_event_rejects_progress_out_of_bounds():
    with pytest.raises(ValidationError):
        RunStreamEvent(
            type="started",
            run_id="run_1",
            run_type="research_room",
            phase="start",
            progress=1.4,
            message="bad progress",
        )


def test_run_record_rejects_invalid_status():
    with pytest.raises(ValidationError):
        RunRecord(
            user_id="user_1",
            run_type="research_room",
            status="done",
        )
