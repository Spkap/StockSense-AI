from fastapi.testclient import TestClient

from stocksense.main import app


def test_research_room_route_requires_auth():
    client = TestClient(app)
    response = client.get("/api/research-room/AMD/stream?question=Is%20AI%20real")

    assert response.status_code == 401


def test_research_room_route_rejects_invalid_ticker(monkeypatch):
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})

    client = TestClient(app)
    response = client.get(
        "/api/research-room/AMD1/stream?question=Is%20AMD%20AI%20real%3F",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 400
    assert "invalid characters" in response.json()["detail"]


def test_research_room_route_returns_sse_for_valid_user(monkeypatch):
    async def fake_stream(*args, **kwargs):
        from stocksense.core.run_schemas import RunStreamEvent

        yield RunStreamEvent(
            type="started",
            run_id="run_1",
            run_type="research_room",
            ticker="AMD",
            phase="start",
            progress=0.1,
            message="Starting",
        )

    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.research_room_routes.run_research_room_stream", fake_stream)

    client = TestClient(app)
    response = client.get(
        "/api/research-room/AMD/stream?question=Is%20AMD%20AI%20real%3F",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data:" in response.text


def test_get_research_room_run_returns_bundle(monkeypatch):
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr(
        "stocksense.api.research_room_routes.get_agent_run_bundle",
        lambda user_id, run_id: {
            "run": {"id": run_id, "user_id": user_id, "run_type": "research_room", "status": "completed"},
            "steps": [],
        },
    )

    client = TestClient(app)
    response = client.get(
        "/api/research-room-runs/run_1",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["run"]["id"] == "run_1"


def test_cancel_research_room_run_persists_cancelled_state(monkeypatch):
    calls = []
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr("stocksense.api.research_room_routes.cancel_agent_run", lambda run_id, user_id: calls.append((run_id, user_id)))

    client = TestClient(app)
    response = client.post(
        "/api/research-room-runs/run_1/cancel",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json() == {"run_id": "run_1", "status": "cancelled"}
    assert calls == [("run_1", "user_1")]


def test_research_room_thesis_draft_endpoint(monkeypatch):
    monkeypatch.setattr("stocksense.api.auth_routes.verify_user_token", lambda token: {"id": "user_1", "email": "a@test.com"})
    monkeypatch.setattr(
        "stocksense.api.research_room_routes.get_agent_run_bundle",
        lambda user_id, run_id: {
            "run": {
                "id": run_id,
                "user_id": user_id,
                "run_type": "research_room",
                "final_result": {
                    "thesis_draft": {
                        "ticker": "AMD",
                        "thesis_summary": "AMD AI thesis is partially supported.",
                        "conviction_level": "medium",
                        "kill_criteria": ["AI server revenue stalls."],
                        "time_horizon": "medium",
                        "thesis_type": "growth",
                        "evidence_refs": ["fact_revenue_01"],
                    }
                },
            },
            "steps": [],
        },
    )

    client = TestClient(app)
    response = client.post(
        "/api/research-room-runs/run_1/thesis-draft",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["thesis_draft"]["ticker"] == "AMD"
