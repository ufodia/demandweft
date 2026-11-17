#!/usr/bin/env python3
"""Deterministic contract-boundary tests; no network or fixture writes."""

import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).with_name("validate_contract.py")
EXAMPLE = SCRIPT.parent.parent / "assets" / "contract.example.json"
SPEC = importlib.util.spec_from_file_location("validate_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASE = MODULE.parse_contract(EXAMPLE.read_text(encoding="utf-8"))


class ContractTests(unittest.TestCase):
    def contract(self):
        return copy.deepcopy(BASE)

    def assert_code(self, contract, expected):
        code, result = MODULE.validate_contract(contract)
        self.assertEqual(code, expected, result)
        self.assertEqual(result["exit_code"], expected)
        self.assertTrue(result["manual_checks"])
        self.assertIn("not approval", result["caveat"])
        return result

    def actual_evidence(self, contract, kind="measurement", independent=False):
        item = contract["evidence"][1]
        item.update(type="observed", kind=kind, independent=independent)

    def test_example_is_a_structurally_reviewable_synthetic_demo(self):
        result = self.assert_code(self.contract(), 0)
        self.assertEqual(result["status"], "ready_for_review")
        self.assertTrue(BASE["demo_only"])
        self.assertEqual({e["type"] for e in BASE["evidence"]}, {"synthetic"})

    def test_unresolved_evidence_and_public_claim_ids_are_blocked(self):
        for route in ("claim", "public", "buyer", "experience"):
            c = self.contract()
            if route == "claim":
                c["claims"][0]["evidence_ids"] = ["missing"]
            elif route == "public":
                c["public"]["claim_ids"] = ["missing"]
            elif route == "buyer":
                c["buyer"]["evidence_ids"] = ["missing"]
            else:
                c["experience"]["verification_evidence_ids"] = ["missing"]
            with self.subTest(route=route):
                self.assert_code(c, 2)

    def test_duplicate_ids_and_references_are_blocked(self):
        for name in ("evidence", "claims"):
            c = self.contract()
            c[name].append(copy.deepcopy(c[name][0]))
            self.assert_code(c, 2)
        c = self.contract()
        c["claims"][0]["evidence_ids"] *= 2
        self.assert_code(c, 2)
        c = self.contract()
        c["public"]["claim_ids"] *= 2
        self.assert_code(c, 2)

    def test_synthetic_or_inferred_evidence_cannot_support_claims(self):
        for kind in ("synthetic", "inferred"):
            for category in ("capability", "descriptive_outcome", "causal_outcome", "testimonial"):
                c = self.contract()
                c["evidence"][1]["type"] = kind
                c["claims"][0].update(status="supported", category=category)
                with self.subTest(kind=kind, category=category):
                    self.assert_code(c, 2)

    def test_demo_does_not_establish_commercial_outcomes(self):
        c = self.contract()
        self.actual_evidence(c, "demonstration")
        c["claims"][0].update(status="supported", category="descriptive_outcome")
        self.assert_code(c, 2)

    def test_causal_claim_requires_independent_measurement_and_manual_review(self):
        c = self.contract()
        self.actual_evidence(c)
        c["claims"][0].update(status="supported", category="causal_outcome")
        self.assert_code(c, 2)
        c["evidence"][1]["independent"] = True
        result = self.assert_code(c, 0)
        self.assertTrue(any("causal" in check for check in result["manual_checks"]))

    def test_feature_comparison_accepts_actual_reference_but_performance_does_not(self):
        c = self.contract()
        self.actual_evidence(c, "reference")
        c["claims"][0].update(status="supported", category="comparison", comparison_basis="features")
        self.assert_code(c, 0)
        c["claims"][0]["comparison_basis"] = "performance"
        self.assert_code(c, 2)
        del c["claims"][0]["comparison_basis"]
        self.assert_code(c, 1)

    def test_comparison_basis_is_forbidden_on_other_categories_even_when_empty(self):
        for category in ("capability", "descriptive_outcome", "causal_outcome", "testimonial"):
            for value in (None, "", "   ", "features", "performance"):
                c = self.contract()
                c["claims"][0].update(category=category, comparison_basis=value)
                with self.subTest(category=category, value=value):
                    result = self.assert_code(c, 2)
                    self.assertTrue(any(error["path"] == "$.claims[0].comparison_basis"
                                        for error in result["errors"]))

    def test_buyer_without_actual_customer_evidence_remains_hypothesis(self):
        c = self.contract()
        c["buyer"]["status"] = "supported"
        self.assert_code(c, 2)

    def test_verified_experience_requires_actual_evidence(self):
        c = self.contract()
        c["experience"].update(implementation_state="verified", verification_evidence_ids=["fictional-proof-text"])
        self.assert_code(c, 2)
        self.actual_evidence(c, "implementation")
        self.assert_code(c, 0)

    def test_planned_deliverable_is_draft_even_when_requested_ready(self):
        c = self.contract()
        c["experience"]["implementation_state"] = "planned"
        self.assert_code(c, 1)

    def test_public_hypotheses_and_unlabeled_illustrations_are_blocked(self):
        c = self.contract()
        c["claims"][0]["status"] = "hypothesis"
        self.assert_code(c, 2)
        for key in ("demo_only", "explicitly_demo"):
            c = self.contract()
            c[key] = False
            self.assert_code(c, 2)

    def test_identical_success_metrics_or_definitions_are_blocked(self):
        for key in ("metric", "success_definition"):
            c = self.contract()
            original = c["success"]["user_value"][key]
            c["success"]["business_outcome"][key] = "  " + original.upper() + "  "
            self.assert_code(c, 2)

    def test_forced_sharing_and_missing_recipient_value(self):
        c = self.contract()
        c["propagation"]["forced_sharing"] = True
        self.assert_code(c, 2)
        c = self.contract()
        del c["propagation"]["recipient_value"]
        self.assert_code(c, 1)

    def test_no_propagation_mode_needs_no_recipient_metric(self):
        c = self.contract()
        c["propagation"] = {"mode": "none", "forced_sharing": False}
        self.assert_code(c, 2)
        del c["success"]["propagation_outcome"]
        self.assert_code(c, 0)

    def test_missing_non_fit_branch_and_budget_stay_draft(self):
        for section, field in (("experience", "non_fit_outcome"), ("budget", "max_cash")):
            c = self.contract()
            del c[section][field]
            self.assert_code(c, 1)
        c = self.contract()
        del c["budget"]
        self.assert_code(c, 1)

    def test_invalid_number_types_and_schema_version(self):
        for value in (True, False, -1, "0", None, float("nan"), float("inf")):
            c = self.contract()
            c["budget"]["max_cash"] = value
            with self.subTest(value=value):
                self.assert_code(c, 2)
        for value in (True, "1", 1.0, 2):
            c = self.contract()
            c["schema_version"] = value
            self.assert_code(c, 2)

    def test_contract_identity_and_schema_version_are_required_for_validation(self):
        for key in ("id", "schema_version"):
            for value in (None, "", "   "):
                c = self.contract()
                c[key] = value
                with self.subTest(key=key, value=value):
                    self.assert_code(c, 2)
            c = self.contract()
            del c[key]
            with self.subTest(key=key, missing=True):
                self.assert_code(c, 2)

    def test_json_duplicate_keys_and_nonfinite_numbers_are_rejected_globally(self):
        for raw in ('{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}',
                    '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                MODULE.parse_contract(raw)

    def test_malformed_evidence_types_do_not_crash(self):
        for key in ("type", "kind"):
            c = self.contract()
            c["evidence"][1][key] = []
            c["claims"][0]["status"] = "supported"
            self.assert_code(c, 2)

    def test_typo_fields_are_not_silently_ignored(self):
        c = self.contract()
        c["auto_publish"] = True
        self.assert_code(c, 2)

    def test_cli_outputs_json_and_does_not_modify_input(self):
        before = EXAMPLE.read_bytes()
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = MODULE.main([str(EXAMPLE)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["exit_code"], 0)
        self.assertEqual(before, EXAMPLE.read_bytes())

    def test_cli_accepts_utf8_bom_and_rejects_non_utf8(self):
        raw = EXAMPLE.read_bytes()
        cases = ((b"\xef\xbb\xbf" + raw, 0),
                 (raw.decode("utf-8").encode("utf-16"), 2))
        for data, expected in cases:
            stdout = io.StringIO()
            with self.subTest(expected=expected):
                with patch.object(Path, "open", return_value=io.BytesIO(data)), \
                        patch("sys.stdout", stdout):
                    self.assertEqual(MODULE.main([str(EXAMPLE)]), expected)
                self.assertEqual(json.loads(stdout.getvalue())["exit_code"], expected)

    def test_cli_usage_failure_is_json(self):
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(MODULE.main([]), 2)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
