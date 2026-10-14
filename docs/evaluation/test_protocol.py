"""Synthetic-only validation; không đọc/chạy Set A/B, DB hoặc model."""

from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from protocol_validation import (
    GOLD_RULES,
    criterion_summary,
    outcome,
    proportion,
    summarize,
    validate_cases,
    validate_manifest,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def case(case_id: str, rule: str) -> dict:
    route, stop = GOLD_RULES[rule]
    return {
        "id": case_id,
        "is_synthetic": True,
        "gold_version": "SYNTHETIC-v1",
        "input": {
            "sender": "synthetic@example.test",
            "subject": "Synthetic contract check",
            "body": "Synthetic metadata validation only.",
            "received_at": "2026-10-14T00:00:00Z",
        },
        "expected_decision": route,
        "expected_type": stop,
        "expected_rule_id": rule,
    }


def row(case_id: str, rule: str) -> dict:
    route, stop = GOLD_RULES.get(rule, ("ERROR", None))
    return {"case_id": case_id, "actual_decision": route, "actual_type": stop, "rule_id": rule}


class ProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.network_guards = [
            patch.object(socket.socket, name, side_effect=AssertionError("OFFLINE_ONLY"))
            for name in ("connect", "connect_ex", "sendto")
        ]
        cls.network_guards += [
            patch.object(socket, name, side_effect=AssertionError("OFFLINE_ONLY"))
            for name in ("create_connection", "getaddrinfo")
        ]
        for guard in cls.network_guards:
            guard.start()
            cls.addClassCleanup(guard.stop)
        cls.schema = json.loads((HERE / "M4_T01_SCHEMA.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def test_wilson_known_values_and_empty(self) -> None:
        expected = {
            (0, 1): (0, 0.7934506856227626),
            (1, 1): (0.20654931437723745, 1),
            (1, 2): (0.09453120573423074, 0.9054687942657693),
            (5, 10): (0.236593090512564, 0.7634069094874361),
            (0, 10): (0, 0.2775327998628892),
            (10, 10): (0.7224672001371107, 1),
        }
        for (n, total), limits in expected.items():
            with self.subTest(n=n, total=total):
                actual = proportion(n, total)
                self.assertEqual((actual["n"], actual["N"]), (n, total))
                for found, wanted in zip(actual["wilson95"], limits):
                    self.assertAlmostEqual(found, wanted, places=12)
        self.assertEqual(
            proportion(0, 0),
            {"n": 0, "N": 0, "rate": None, "wilson95": None, "status": "UNDEFINED"},
        )

    def test_wilson_bounds_and_symmetry(self) -> None:
        for total in range(1, 31):
            for n in range(total + 1):
                lo, hi = proportion(n, total)["wilson95"]
                other_lo, other_hi = proportion(total - n, total)["wilson95"]
                self.assertTrue(0 <= lo <= n / total + 1e-15)
                self.assertTrue(n / total - 1e-15 <= hi <= 1)
                self.assertAlmostEqual(lo, 1 - other_hi)
                self.assertAlmostEqual(hi, 1 - other_lo)

    def test_wilson_rejects_invalid_counts(self) -> None:
        for pair in ((-1, 2), (3, 2), (0, -1), (True, 1), (1, 1.5)):
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                proportion(*pair)

    def test_confusion_failures_and_denominators(self) -> None:
        cases = [
            case(str(i), rule)
            for i, rule in enumerate(
                ("P05", "P01", "P02", "P05", "P03", "P01", "P05", "P05", "P02")
            )
        ]
        rows = [
            row(str(i), rule)
            for i, rule in enumerate(("P05", "P01", "P05", "P02", "P02", "TECHNICAL_ERROR"))
        ]
        # 6 absent; 7 malformed; 8 is INVALID_INPUT for a valid business case.
        rows += [
            {**row("7", "P05"), "actual_decision": "UNKNOWN"},
            {**row("8", "P05"), "actual_decision": "INVALID_INPUT"},
        ]
        result = summarize(cases, rows)
        self.assertEqual(result["confusion"], {"TP": 2, "FN": 1, "FP": 1, "TN": 1})
        self.assertEqual(
            result["outcomes"],
            {"VALID": 5, "TECHNICAL_ERROR": 1, "MALFORMED": 1, "MISSING": 1, "INVALID_INPUT": 1},
        )
        expected = {
            "MER": (1, 3),
            "OER": (1, 2),
            "escalation_precision": (2, 3),
            "escalation_recall": (2, 3),
            "coverage": (5, 9),
            "technical_failure": (2, 9),
            "missingness": (1, 9),
            "invalid_input": (1, 9),
            "route_correctness": (3, 5),
            "end_to_end_route_success": (3, 9),
            "stop_correctness": (1, 3),
            "conditional_stop_correctness": (1, 2),
            "rule_correctness": (2, 5),
        }
        for name, pair in expected.items():
            self.assertEqual((result["metrics"][name]["n"], result["metrics"][name]["N"]), pair)
        self.assertEqual(result["stop_matrix"]["OUT_OF_POLICY"]["AUTO_REPLY"], 1)
        self.assertEqual(result["stop_matrix"]["FACT_UNRESOLVED"]["OUT_OF_POLICY"], 1)
        self.assertEqual(result["by_gold"]["ESCALATE"]["TECHNICAL_ERROR"], 1)
        self.assertEqual(
            result["missing_outcome_bounds"]["ESCALATE"],
            {"planned": 5, "nonbusiness": 2, "lower": 0.2, "upper": 0.6},
        )
        self.assertEqual(
            result["missing_outcome_bounds"]["AUTO_REPLY"],
            {"planned": 4, "nonbusiness": 2, "lower": 0.25, "upper": 0.75},
        )

    def test_rule_and_stop_mismatch_stay_business(self) -> None:
        result = summarize([case("s", "P03")], [row("s", "P04")])
        self.assertEqual(result["metrics"]["stop_correctness"]["rate"], 1)
        self.assertEqual(result["metrics"]["rule_correctness"]["rate"], 0)
        self.assertEqual(result["metrics"]["technical_failure"]["n"], 0)
        inconsistent = {**row("s", "P01"), "actual_type": "OUT_OF_POLICY"}
        self.assertEqual(outcome(inconsistent), "VALID")

    def test_empty_and_all_failure_populations(self) -> None:
        result = summarize([], [])
        self.assertTrue(all(m["status"] == "UNDEFINED" for m in result["metrics"].values()))
        result = summarize([case("a", "P01")], [row("a", "TECHNICAL_ERROR")])
        self.assertEqual(result["metrics"]["MER"]["status"], "UNDEFINED")
        self.assertEqual(result["metrics"]["technical_failure"]["rate"], 1)
        self.assertEqual(result["metrics"]["end_to_end_route_success"]["rate"], 0)

    def test_ids_and_gold_are_not_silently_repaired(self) -> None:
        for cases, rows in (
            ([case("a", "P01")] * 2, []),
            ([case("a", "P01")], [row("x", "P01")]),
            ([case("a", "P01")], [row("a", "P01")] * 2),
            ([{**case("a", "P01"), "expected_type": "OUT_OF_POLICY"}], []),
        ):
            with self.subTest(cases=cases, rows=rows), self.assertRaises(ValueError):
                summarize(cases, rows)

    def test_malformed_and_technical_are_distinct(self) -> None:
        for value in (
            {},
            {**row("a", "P05"), "actual_type": "FACT_UNRESOLVED"},
            {**row("a", "P01"), "actual_type": None},
            {**row("a", "P01"), "actual_type": []},
            {**row("a", "TECHNICAL_ERROR"), "rule_id": "P04"},
        ):
            self.assertEqual(outcome(value), "MALFORMED")
        self.assertEqual(outcome(row("a", "TECHNICAL_ERROR")), "TECHNICAL_ERROR")
        self.assertEqual(outcome(None), "MISSING")

    def test_schema_result_normalization(self) -> None:
        for rule in GOLD_RULES.keys() | {"TECHNICAL_ERROR"}:
            value = {
                **row("s", rule),
                "elapsed_ms": 1,
                "outcome": "TECHNICAL_ERROR" if rule == "TECHNICAL_ERROR" else "VALID",
                "error_code": "SYNTHETIC_TIMEOUT" if rule == "TECHNICAL_ERROR" else None,
                "artifact_ref": "synthetic-result",
            }
            self.validator.validate(value)
            self.assertEqual(outcome(value), value["outcome"])
        for category in ("MISSING", "MALFORMED"):
            value = {
                "case_id": "s",
                "actual_decision": None,
                "actual_type": None,
                "rule_id": None,
                "elapsed_ms": None,
                "outcome": category,
                "error_code": "SYNTHETIC_ABSENT",
                "artifact_ref": None,
            }
            self.validator.validate(value)
            self.assertEqual(outcome(value), category)
        bad = {**value, "outcome": "VALID", "actual_decision": "ESCALATE", "rule_id": "P01"}
        self.assertFalse(self.validator.is_valid(bad))
        bad = {**value, "actual_decision": "AUTO_REPLY"}
        self.assertFalse(self.validator.is_valid(bad))

    def test_schema_case_and_timestamp(self) -> None:
        for rule in GOLD_RULES:
            self.validator.validate(case("s", rule))
        bad = case("s", "P05")
        bad["input"]["received_at"] = "2026-10-14T00:00:00"
        self.assertFalse(self.validator.is_valid(bad))
        with self.assertRaises(ValueError):
            validate_cases([bad])
        bad["input"]["received_at"] = "2026-02-30T00:00:00Z"
        with self.assertRaises(ValueError):
            validate_cases([bad])

    def test_content_review_denominators(self) -> None:
        result = criterion_summary(["PASS", "FAIL", "NOT_REVIEWED"])
        for key, pair in (
            ("success", (1, 3)),
            ("review_coverage", (2, 3)),
            ("reviewed_only", (1, 2)),
        ):
            self.assertEqual((result[key]["n"], result[key]["N"]), pair)
        self.assertEqual(result["not_reviewed"], 1)
        self.assertEqual(criterion_summary([])["success"]["status"], "UNDEFINED")
        with self.assertRaises(ValueError):
            criterion_summary(["NOT_APPLICABLE"])

    def test_manifest_exact_bytes_and_rejected_drift(self) -> None:
        cases = [case("s", "P05")]
        data = json.dumps(cases).encode()
        protocol = (HERE / "M4_T01_PROTOCOL.md").read_bytes()
        manifest = {
            "protocol_version": "M4-T01-v1",
            "protocol_sha256": sha256(protocol).hexdigest(),
            "dataset_id": "SYNTHETIC_ONLY",
            "dataset_sha256": sha256(data).hexdigest(),
            "gold_version": "SYNTHETIC-v1",
            "case_ids": ["s"],
            "planned_count": 1,
            "runtime_sha": "eaaeea88a59618b49219a20ae01a3cf3227cec87",
            "mode": "OFFLINE_UNIT",
            "eligibility": "SYNTHETIC_ONLY",
            "execution_authorized": False,
            "official_config": None,
            "pending_authorization": ["Official configuration and GO are not granted"],
        }
        self.validator.validate(manifest)
        validate_manifest(manifest, data, protocol)
        for key, value in (
            ("case_ids", ["other"]),
            ("planned_count", 2),
            ("dataset_sha256", "0" * 64),
            ("protocol_sha256", "0" * 64),
            ("gold_version", "OTHER"),
            ("execution_authorized", True),
        ):
            changed = {**manifest, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_manifest(changed, data, protocol)
        with self.assertRaises(ValueError):
            validate_manifest(manifest, data + b"\n", protocol)
        self.assertFalse(self.validator.is_valid({**manifest, "execution_authorized": True}))

    def test_source_harness_contract_without_importing_app(self) -> None:
        source = ast.parse((ROOT / "verify/harness.py").read_text(encoding="utf-8"))
        definitions = {node.name: node for node in source.body if isinstance(node, ast.ClassDef)}
        fields = {
            node.target.id
            for node in definitions["VerifyResult"].body
            if isinstance(node, ast.AnnAssign)
        }
        self.assertTrue(
            {
                "case_id",
                "actual_decision",
                "actual_type",
                "rule_id",
                "elapsed_ms",
                "timestamp",
                "corpus_version",
                "case_ref",
                "passed",
            }
            <= fields
        )
        source = ast.parse((ROOT / "core/types.py").read_text(encoding="utf-8"))
        enums = {
            node.name: {
                assignment.value.value
                for assignment in node.body
                if isinstance(assignment, ast.Assign)
            }
            for node in source.body
            if isinstance(node, ast.ClassDef) and node.name in {"Decision", "EscalationType"}
        }
        self.assertEqual(enums["Decision"], {"AUTO_REPLY", "ESCALATE", "INVALID_INPUT", "ERROR"})
        self.assertEqual(
            enums["EscalationType"], {stop for _, stop in GOLD_RULES.values()} - {None}
        )


if __name__ == "__main__":
    unittest.main()
