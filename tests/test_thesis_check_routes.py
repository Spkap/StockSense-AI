from fastapi.testclient import TestClient

from stocksense.main import app


def test_thesis_check_route_requires_auth():
    client = TestClient(app)
    response = client.get("/api/theses/thesis_1/check/stream")

    assert response.status_code == 401


def test_thesis_check_route_returns_sse_for_valid_user(monkeypatch):
    from unittest.mock import MagicMock

    async def fake_stream(*args, **kwargs):
        from stocksense.core.thesis_forensics_schemas import ThesisCheckStreamEvent

        yield ThesisCheckStreamEvent(
            type="started",
            run_id="run_1",
            thesis_id="thesis_1",
            ticker="AAPL",
            phase="start",
            progress=0.1,
            message="Starting",
        )

    fake_client = MagicMock()
    thesis_response = MagicMock()
    thesis_response.data = {
        "id": "thesis_1",
        "user_id": "user_1",
        "ticker": "AAPL",
        "thesis_summary": "Apple AI thesis",
    }
    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = thesis_response

    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.thesis_check_routes.get_supabase_client", lambda: fake_client)
    monkeypatch.setattr("stocksense.api.thesis_check_routes.run_thesis_check_stream", fake_stream)

    client = TestClient(app)
    response = client.get(
        "/api/theses/thesis_1/check/stream",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data:" in response.text


def test_latest_thesis_check_returns_bundle_for_valid_user(monkeypatch):
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr(
        "stocksense.api.thesis_check_routes._load_user_thesis",
        lambda user_id, access_token, thesis_id: {"id": thesis_id, "ticker": "AAPL"},
    )
    monkeypatch.setattr(
        "stocksense.api.thesis_check_routes.get_latest_thesis_check_run_bundle",
        lambda user_id, thesis_id: {
            "run": {"id": "run_1", "thesis_id": thesis_id, "status": "completed"},
            "steps": [],
            "evidence": [],
        },
    )

    client = TestClient(app)
    response = client.get(
        "/api/theses/thesis_1/check/latest",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["run"]["id"] == "run_1"


def test_cancel_thesis_run_persists_cancelled_state(monkeypatch):
    calls = []

    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr(
        "stocksense.api.thesis_check_routes.cancel_thesis_check_run",
        lambda run_id, user_id: calls.append((run_id, user_id)),
    )

    client = TestClient(app)
    response = client.post(
        "/api/thesis-runs/run_1/cancel",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json() == {"run_id": "run_1", "status": "cancelled"}
    assert calls == [("run_1", "user_1")]


def test_add_thesis_run_correction_persists_user_feedback(monkeypatch):
    saved_payloads = []

    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr(
        "stocksense.api.thesis_check_routes.get_thesis_check_run_bundle",
        lambda user_id, run_id: {
            "run": {"id": run_id, "user_id": user_id, "thesis_id": "thesis_1"},
            "steps": [],
            "evidence": [],
        },
    )

    def fake_save(**kwargs):
        saved_payloads.append(kwargs)
        return {"id": "correction_1", **kwargs}

    monkeypatch.setattr("stocksense.api.thesis_check_routes.save_thesis_correction", fake_save)

    client = TestClient(app)
    response = client.post(
        "/api/thesis-runs/run_1/corrections",
        headers={"Authorization": "Bearer token"},
        json={
            "correction_type": "evidence_irrelevant",
            "correction_text": "Not relevant",
            "claim": "AI claim",
            "evidence_local_id": "news_01",
        },
    )

    assert response.status_code == 200
    assert response.json()["correction"]["id"] == "correction_1"
    assert saved_payloads[0]["thesis_id"] == "thesis_1"
    assert saved_payloads[0]["correction_type"] == "evidence_irrelevant"
