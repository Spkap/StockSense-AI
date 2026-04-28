from unittest.mock import patch

from stocksense.orchestration.falsifiability_compiler import compile_thesis_to_world_model, persist_world_model


def test_compile_thesis_to_world_model_creates_claims_with_observables_or_gaps():
    thesis = {
        "id": "thesis_1",
        "ticker": "AMD",
        "thesis_summary": "AMD AI server revenue will grow materially. Gross margin should improve as accelerators scale.",
        "conviction_level": "medium",
        "time_horizon": "medium",
        "kill_criteria": ["AI server revenue stalls", "Gross margin compresses"],
    }

    result = compile_thesis_to_world_model(thesis)

    assert result.thesis_id == "thesis_1"
    assert 3 <= len(result.claims) <= 7
    assert all(claim.observables or claim.evidence_needed for claim in result.claims)
    assert len(result.forecast_questions) == len(result.claims)


def test_compile_thesis_to_world_model_handles_single_sentence_summary():
    thesis = {
        "id": "thesis_1",
        "ticker": "AAPL",
        "thesis_summary": "Apple services revenue growth supports durable margins",
        "conviction_level": "high",
        "time_horizon": "long",
        "kill_criteria": [],
    }

    result = compile_thesis_to_world_model(thesis)

    assert result.claims[0].claim_type == "growth"
    assert result.claims[0].observables[0].source_type == "sec_company_facts"


def test_persist_world_model_returns_persisted_claim_and_forecast_ids():
    thesis = {
        "id": "thesis_1",
        "ticker": "AMD",
        "thesis_summary": "AMD AI server revenue will grow materially.",
        "conviction_level": "medium",
        "time_horizon": "medium",
        "kill_criteria": [],
    }
    result = compile_thesis_to_world_model(thesis)

    class FakeResponse:
        def __init__(self, data):
            self.data = data

    class FakeQuery:
        claim_count = 0
        forecast_count = 0

        def __init__(self, table_name):
            self.table_name = table_name

        def insert(self, payload):
            self.payload = payload
            return self

        def execute(self):
            if self.table_name == "thesis_claims":
                FakeQuery.claim_count += 1
                return FakeResponse([{"id": f"claim_{FakeQuery.claim_count}"}])
            if self.table_name == "forecast_questions":
                FakeQuery.forecast_count += 1
                return FakeResponse([{"id": f"forecast_{FakeQuery.forecast_count}"}])
            return FakeResponse([{}])

    class FakeClient:
        def table(self, table_name):
            return FakeQuery(table_name)

    with patch("stocksense.orchestration.falsifiability_compiler.get_supabase_admin_client", return_value=FakeClient()):
        persisted = persist_world_model("user_1", "thesis_1", result)

    assert persisted.claims[0].id == "claim_1"
    assert persisted.forecast_questions[0].id == "forecast_1"
    assert persisted.forecast_questions[0].claim_id == "claim_1"
