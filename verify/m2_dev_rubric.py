"""Mapping review-only cho frozen rubric; không thay gold hay production routing.

Mỗi vị trí là đúng index trong nhóm meta tương ứng, không suy từ nhãn reviewer.
G bao gồm claims/assumptions/coverage trong output; Q/O chỉ dùng khi criterion
nói tới question/options; T cho temporal/current policy; S cho conflict handling.
"""

CODES = {
    "D": "decision_match",
    "E": "escalation_type_match",
    "R": "rule_id_match",
    "G": "grounding_and_citation",
    "Q": "question_quality",
    "O": "options_quality",
    "T": "temporal_safety",
    "S": "selective_conflict_handling",
}
GROUPS = ("pass_criteria", "fail_signals", "forbidden_assumptions")
# Cùng thứ tự với frozen rubric. Multi-code = cần judgment cho TẤT CẢ dimensions.
MAPPING = {
    "M2DEV-A1": (
        ("DER", "GQO", "G", "G"),
        ("D", "O", "G", "R"),
        ("G", "G", "G", "G"),
    ),
    "M2DEV-A2": (
        ("DERS", "GO", "G", "G"),
        ("D", "O", "RS", "G"),
        ("G", "G", "GS", "G", "G"),
    ),
    "M2DEV-A3": (
        ("DER", "GO", "G"),
        ("D", "GO", "O", "G"),
        ("GT", "G", "G", "G", "G"),
    ),
    "M2DEV-A4": (
        ("DER", "G", "G", "G", "G"),
        ("DG", "R", "R", "O", "G"),
        ("G", "G", "G", "G"),
    ),
    "M2DEV-B1": (
        ("DER", "QT", "GT"),
        ("DGT", "GT", "R"),
        ("GT", "GT", "GT", "GT"),
    ),
    "M2DEV-B2": (
        ("DR", "G", "GT"),
        ("D", "G", "GT"),
        ("G", "GT", "G", "G"),
    ),
    "M2DEV-B3": (
        ("DER", "GS", "G"),
        ("DGS", "GS", "R"),
        ("GS", "GS", "G", "GS"),
    ),
    "M2DEV-B4": (
        ("DR", "G", "GS"),
        ("DS", "GS"),
        ("GS", "GS", "G"),
    ),
    "M2DEV-C1": (
        ("DR", "G", "GT", "GT"),
        ("GT", "G", "D"),
        ("GT", "G", "GT"),
    ),
    "M2DEV-C2": (
        ("DER", "QT", "GT", "G"),
        ("DGT", "GT", "QT", "R", "O"),
        ("GT", "G", "GT", "GT"),
    ),
    "M2DEV-C3": (
        ("DR", "GT", "G"),
        ("D", "GT", "G"),
        ("GT", "G", "G"),
    ),
    "M2DEV-C4": (
        ("DER", "G", "G", "GT", "G"),
        ("D", "R", "G", "G"),
        ("G", "GT", "G", "GT"),
    ),
}


def criterion_dimensions(case_id: str) -> dict[str, tuple[str, ...]]:
    """Public mapping kiểm được offline, bound với hash fixture tại caller."""
    return {
        f"{group}:{i}": tuple(CODES[code] for code in codes)
        for group, rows in zip(GROUPS, MAPPING[case_id], strict=True)
        for i, codes in enumerate(rows)
    }
