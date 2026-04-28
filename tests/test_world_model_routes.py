from fastapi.testclient import TestClient

from stocksense.core.world_model_schemas import ClaimObservable, ForecastQuestion, ThesisClaim
from stocksense.main import app


def test_compile_route_requires_auth():
    client = TestClient(app)
    response = client.post("/api/theses/thesis_1/compile")

    assert response.status_code == 401


def test_compile_route_returns_claim_graph(monkeypatch):
    thesis = {
        "id": "thesis_1",
        "ticker": "AMD",
        "thesis_summary": "AMD AI server revenue will grow materially. Gross margin should improve.",
        "conviction_level": "medium",
        "time_horizon": "medium",
        "kill_criteria": ["Revenue stalls"],
    }
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.world_model_routes._load_user_thesis", lambda user_id, thesis_id: thesis)
    monkeypatch.setattr("stocksense.api.world_model_routes._load_claims", lambda thesis_id, user_id: [])
    monkeypatch.setattr("stocksense.api.world_model_routes.persist_world_model", lambda user_id, thesis_id, result: result)

    client = TestClient(app)
    response = client.post(
        "/api/theses/thesis_1/compile",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["ticker"] == "AMD"
    assert response.json()["claims"]


def test_compile_route_returns_existing_world_model_without_duplication(monkeypatch):
    thesis = {
        "id": "thesis_1",
        "ticker": "AMD",
        "thesis_summary": "AMD AI server revenue will grow materially.",
        "conviction_level": "medium",
        "time_horizon": "medium",
        "kill_criteria": ["Revenue stalls"],
    }
    existing_claim = ThesisClaim(
        id="claim_1",
        claim_text="AMD AI server revenue will grow materially.",
        claim_type="growth",
        confidence="medium",
        evidence_needed=["Revenue by segment"],
        observables=[ClaimObservable(observable_name="Track revenue", source_type="sec_company_facts", metric_key="revenue")],
    )
    existing_forecast = ForecastQuestion(
        id="forecast_1",
        claim_id="claim_1",
        question="Will revenue validate the claim?",
        resolution_criteria="Use SEC company facts.",
        probability=0.55,
    )
    persisted_calls = []

    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.world_model_routes._load_user_thesis", lambda user_id, thesis_id: thesis)
    monkeypatch.setattr("stocksense.api.world_model_routes._load_claims", lambda thesis_id, user_id: [existing_claim])
    monkeypatch.setattr("stocksense.api.world_model_routes._load_forecast_questions", lambda thesis_id, user_id: [existing_forecast])
    monkeypatch.setattr("stocksense.api.world_model_routes.persist_world_model", lambda *args, **kwargs: persisted_calls.append(args))

    client = TestClient(app)
    response = client.post(
        "/api/theses/thesis_1/compile",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["claims"][0]["id"] == "claim_1"
    assert response.json()["forecast_questions"][0]["id"] == "forecast_1"
    assert persisted_calls == []


def test_scenario_route_returns_three_paths(monkeypatch):
    thesis = {
        "id": "thesis_1",
        "ticker": "AMD",
        "thesis_summary": "AMD AI server revenue will grow materially.",
        "conviction_level": "medium",
        "time_horizon": "medium",
        "kill_criteria": [],
    }
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.world_model_routes._load_user_thesis", lambda user_id, thesis_id: thesis)
    monkeypatch.setattr("stocksense.api.world_model_routes._load_claims", lambda thesis_id, user_id: [])
    monkeypatch.setattr("stocksense.api.world_model_routes.persist_scenario_board", lambda *args, **kwargs: None)

    client = TestClient(app)
    response = client.post(
        "/api/theses/thesis_1/scenarios",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert [scenario["scenario"] for scenario in response.json()["scenarios"]] == ["bull", "base", "bear"]


def test_resolve_forecast_question_persists_brier_score(monkeypatch):
    updates = []

    class FakeResponse:
        def __init__(self, data):
            self.data = data

    class FakeQuery:
        def __init__(self, table_name):
            self.table_name = table_name
            self.update_payload = None

        def select(self, *_args):
            return self

        def eq(self, *_args):
            return self

        def single(self):
            return self

        def update(self, payload):
            self.update_payload = payload
            updates.append(payload)
            return self

        def execute(self):
            if self.update_payload is not None:
                return FakeResponse([self.update_payload])
            return FakeResponse(
                {
                    "id": "forecast_1",
                    "user_id": "user_1",
                    "probability": 0.8,
                    "status": "open",
                }
            )

    class FakeClient:
        def table(self, table_name):
            return FakeQuery(table_name)

    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.world_model_routes.get_supabase_admin_client", lambda: FakeClient())

    client = TestClient(app)
    response = client.post(
        "/api/forecast-questions/forecast_1/resolve",
        headers={"Authorization": "Bearer token"},
        json={"outcome": True},
    )

    assert response.status_code == 200
    assert response.json()["brier_score"] == 0.04
    assert updates[0]["brier_score"] == 0.04
    assert updates[0]["resolved_outcome"] is True
