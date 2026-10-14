from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from collector import FREEZE_SCHEMA, reconcile, validate_freeze_manifest  # noqa: E402


RUNTIME_SHA = "fe8c2dbca013e9344a678ba52f70588495c897ef"
BINDING = {
    "run_id": "synthetic-run",
    "runtime_source_sha": RUNTIME_SHA,
    "collector_revision": "synthetic-collector",
    "manifest_ref": "synthetic-manifest",
    "config_ref": "synthetic-config",
}


def attempt(case_id: str = "case-1", attempt_id: str = "attempt-1", **changes: object) -> dict:
    value = {
        **BINDING,
        "case_id": case_id,
        "attempt_id": attempt_id,
        "timestamp": "2026-10-15T00:00:00Z",
        "result_status": "BUSINESS_RESULT",
        "terminal": True,
        "business_result": {"decision": "AUTO_REPLY", "stop_type": None, "rule_id": "P05"},
        "technical_failure": None,
        "evidence_ref": "synthetic-evidence",
    }
    value.update(changes)
    return value


class CollectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = json.loads(
            (HERE / "M4_T01_FREEZE_TEMPLATE.json").read_text(encoding="utf-8")
        )

    def test_normal_terminal_result(self) -> None:
        result = reconcile(["case-1"], [attempt()], BINDING)
        self.assertEqual(result["results"][0]["status"], "BUSINESS_RESULT")
        self.assertEqual(result["results"][0]["terminal_outcome"], "BUSINESS_RESULT")
        self.assertTrue(result["complete"])

    def test_technical_error_stays_technical(self) -> None:
        row = attempt(
            result_status="TECHNICAL_ERROR",
            business_result=None,
            technical_failure={"code": "SYNTHETIC_TIMEOUT"},
        )
        result = reconcile(["case-1"], [row], BINDING)["results"][0]
        self.assertEqual(result["status"], "TECHNICAL_ERROR")
        self.assertIsNone(result["business_result"])

    def test_missing_expected_case(self) -> None:
        result = reconcile(["case-1"], [], BINDING)
        self.assertEqual(result["results"][0]["status"], "MISSING")
        self.assertFalse(result["complete"])

    def test_duplicate_attempt_or_terminal_is_detected(self) -> None:
        duplicate = attempt()
        result = reconcile(["case-1"], [duplicate, duplicate], BINDING)
        self.assertEqual(result["results"][0]["status"], "DUPLICATE")

    def test_unexpected_case_is_reported(self) -> None:
        result = reconcile(["case-1"], [attempt("other")], BINDING)
        self.assertEqual([item["status"] for item in result["results"]], ["MISSING", "UNEXPECTED"])

    def test_malformed_result_is_reported(self) -> None:
        row = attempt()
        row.pop("result_status")
        result = reconcile(["case-1"], [row], BINDING)
        self.assertEqual(result["results"][0]["status"], "MALFORMED")

    def test_multiple_attempts_choose_single_terminal(self) -> None:
        retry = attempt(
            attempt_id="attempt-1",
            timestamp="2026-10-15T00:00:00Z",
            result_status="TECHNICAL_ERROR",
            terminal=False,
            business_result=None,
            technical_failure={"code": "SYNTHETIC_RETRY"},
        )
        terminal = attempt(attempt_id="attempt-2", timestamp="2026-10-15T00:00:01Z")
        result = reconcile(["case-1"], [terminal, retry], BINDING)["results"][0]
        self.assertEqual((result["status"], result["attempt_id"]), ("BUSINESS_RESULT", "attempt-2"))

    def test_runtime_sha_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "runtime_source_sha mismatch"):
            reconcile(["case-1"], [attempt(runtime_source_sha="0" * 40)], BINDING)

    def test_manifest_and_config_mismatch_fail_closed(self) -> None:
        for key in ("manifest_ref", "config_ref"):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, f"{key} mismatch"):
                reconcile(["case-1"], [attempt(**{key: "wrong"})], BINDING)

    def test_reconciliation_covers_every_expected_case(self) -> None:
        result = reconcile(["a", "b", "c"], [attempt("a"), attempt("c")], BINDING)
        self.assertEqual([item["case_id"] for item in result["results"]], ["a", "b", "c"])
        self.assertEqual(result["counts"], {"BUSINESS_RESULT": 2, "MISSING": 1})

    def test_freeze_schema_accepts_template(self) -> None:
        Draft202012Validator.check_schema(FREEZE_SCHEMA)
        Draft202012Validator(FREEZE_SCHEMA, format_checker=FormatChecker()).validate(self.template)

    def test_unresolved_freeze_is_incomplete(self) -> None:
        self.assertEqual(
            validate_freeze_manifest(self.template, expected_runtime_sha=RUNTIME_SHA),
            "FREEZE_INCOMPLETE",
        )

    def test_official_readiness_fails_while_unauthorized(self) -> None:
        with self.assertRaisesRegex(ValueError, "OFFICIAL_EXECUTION_READY"):
            validate_freeze_manifest(
                self.template, expected_runtime_sha=RUNTIME_SHA, official_execution_ready=True
            )

    def test_private_fields_are_not_copied(self) -> None:
        private_marker = "PRIVATE-SYNTHETIC-MARKER"
        row = {**attempt(), "private_content": private_marker}
        output = reconcile(["case-1"], [row], BINDING)
        self.assertEqual(output["results"][0]["status"], "MALFORMED")
        self.assertNotIn(private_marker, json.dumps(output))

    def test_freeze_runtime_mismatch_fails_closed(self) -> None:
        changed = deepcopy(self.template)
        changed["runtime_source_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "runtime_source_sha mismatch"):
            validate_freeze_manifest(changed, expected_runtime_sha=RUNTIME_SHA)


if __name__ == "__main__":
    unittest.main()
