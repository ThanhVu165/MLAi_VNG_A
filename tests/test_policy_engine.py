from pathlib import Path

import yaml  # type: ignore[import-untyped]

POLICIES_DIR = Path(__file__).parents[1] / "policies"


def test_policy_configuration_is_valid_and_complete() -> None:
    policy = yaml.safe_load((POLICIES_DIR / "policy.yaml").read_text(encoding="utf-8"))
    blocklist = yaml.safe_load((POLICIES_DIR / "blocklist.yaml").read_text(encoding="utf-8"))
    fallbacks = yaml.safe_load(
        (POLICIES_DIR / "fallback_questions.yaml").read_text(encoding="utf-8")
    )

    assert [rule["id"] for rule in policy["priority_order"]] == ["P01", "P02", "P03", "P04", "P05"]
    assert all(rule["reason_vi"] for rule in policy["priority_order"])
    assert "vui lòng xem xét" in blocklist["phrases"]
    assert set(fallbacks["templates"]) == {
        "FACT_UNRESOLVED",
        "OUT_OF_POLICY",
        "AUTHORITY_REQUIRED",
    }
    for template in fallbacks["templates"].values():
        assert set(template) == {"summary", "facts", "basis", "question", "options"}
        assert 2 <= len(template["options"]) <= 3
