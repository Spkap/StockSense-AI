from stocksense.core.evidence_hashing import hash_evidence_items, has_material_evidence_change
from stocksense.core.thesis_forensics_schemas import EvidenceItem


def test_hash_is_stable_for_same_evidence_in_different_order():
    first = [
        EvidenceItem(source_type="news", source_name="NewsAPI", title="B", text="Second", reliability_tier="medium"),
        EvidenceItem(source_type="news", source_name="NewsAPI", title="A", text="First", reliability_tier="medium"),
    ]
    second = [
        EvidenceItem(source_type="news", source_name="NewsAPI", title="A", text="First", reliability_tier="medium"),
        EvidenceItem(source_type="news", source_name="NewsAPI", title="B", text="Second", reliability_tier="medium"),
    ]

    assert hash_evidence_items(first) == hash_evidence_items(second)


def test_hash_changes_when_text_changes():
    old = [EvidenceItem(source_type="news", source_name="NewsAPI", title="A", text="First", reliability_tier="medium")]
    new = [EvidenceItem(source_type="news", source_name="NewsAPI", title="A", text="Updated", reliability_tier="medium")]

    assert hash_evidence_items(old) != hash_evidence_items(new)


def test_material_change_false_when_hash_matches():
    assert has_material_evidence_change("abc", "abc") is False


def test_material_change_true_when_prior_hash_missing():
    assert has_material_evidence_change(None, "abc") is True
