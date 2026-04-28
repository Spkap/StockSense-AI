from stocksense.core.world_model_schemas import ClaimObservable, ThesisClaim
from stocksense.orchestration.scenario_simulator import build_scenario_board


def test_scenario_board_is_constrained_to_existing_claims():
    thesis = {"id": "thesis_1", "ticker": "AMD"}
    claims = [
        ThesisClaim(
            claim_text="AI server revenue grows",
            claim_type="growth",
            evidence_needed=["Revenue by segment"],
            observables=[ClaimObservable(observable_name="Revenue", source_type="sec_company_facts")],
        ),
        ThesisClaim(
            claim_text="Margins improve",
            claim_type="margin",
            evidence_needed=["Gross margin proof"],
            observables=[ClaimObservable(observable_name="Gross margin", source_type="sec_company_facts")],
        ),
    ]

    result = build_scenario_board(thesis, claims)

    assert [scenario.scenario for scenario in result.scenarios] == ["bull", "base", "bear"]
    assert result.scenarios[0].impacted_claims == ["AI server revenue grows", "Margins improve"]
    assert "Revenue by segment" in result.scenarios[0].evidence_required
