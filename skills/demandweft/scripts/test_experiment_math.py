"""Decision-boundary, input-safety and numerical checks; all tests run offline."""
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import experiment_math as em


def valid_input():
    return {
        "schema_version": 1, "data_kind": "observed",
        "control": {"n": 1000, "successes": 100},
        "treatment": {"n": 1000, "successes": 200},
        "design": {"assignment": "randomized", "allocation_model": "independent_bernoulli",
                   "unit": "person",
                   "independence": "independent", "interference": "absent",
                   "preregistered": True, "fixed_horizon": True,
                   "horizon_status": "complete", "outcome_maturity": "mature",
                   "data_quality": "clear", "minimum_per_arm": 1000,
                   "expected_treatment_allocation": 0.5},
        "minimum_worthwhile_absolute_lift": 0.02,
        "economics": {"currency": "TRY", "contribution_per_success": 100,
                      "extra_cost_for_treatment_sample": 500},
    }


class ExperimentMathTests(unittest.TestCase):
    def test_bounded_followup_and_input_unchanged(self):
        data = valid_input()
        snapshot = copy.deepcopy(data)
        result = em.analyze(data)
        self.assertEqual(result["interpretation"]["label"], "supports_bounded_followup")
        self.assertEqual(data, snapshot)
        self.assertEqual(result["interpretation"]["automatic_action"], "none")

    def test_zero_events_remain_uncertain_and_relative_is_null(self):
        data = valid_input()
        data["control"]["successes"] = data["treatment"]["successes"] = 0
        data["minimum_worthwhile_absolute_lift"] = 0
        data["economics"]["extra_cost_for_treatment_sample"] = 0
        result = em.analyze(data)
        self.assertIsNone(result["comparison"]["relative_lift"])
        low, high = result["comparison"]["interval_95"]
        self.assertLess(low, 0)
        self.assertGreater(high, 0)
        self.assertEqual(result["interpretation"]["label"], "inconclusive")

    def test_all_events_and_one_event_boundaries(self):
        for successes, n in ((0, 1), (1, 1), (1000, 1000), (0, em.MAX_COUNT),
                             (em.MAX_COUNT, em.MAX_COUNT)):
            lo, hi = em.wilson(successes, n)
            self.assertTrue(0 <= lo <= successes / n <= hi <= 1)
            self.assertGreater(hi - lo, 0)
            if successes == 0:
                self.assertEqual(lo, 0.0)
            if successes == n:
                self.assertEqual(hi, 1.0)

    def test_sign_reversal_swaps_interval_endpoints(self):
        a = em.newcombe(35, 100, 20, 100)
        b = em.newcombe(20, 100, 35, 100)
        self.assertAlmostEqual(a[0], -b[1], places=14)
        self.assertAlmostEqual(a[1], -b[0], places=14)
        data = valid_input()
        data["control"], data["treatment"] = data["treatment"], data["control"]
        self.assertEqual(em.analyze(data)["interpretation"]["label"], "revise_or_stop")

    def test_each_design_failure_blocks_a_large_positive_result(self):
        cases = {"assignment": "observational", "unit": "cluster",
                 "independence": "dependent", "interference": "present",
                 "preregistered": False, "fixed_horizon": False,
                 "horizon_status": "incomplete", "outcome_maturity": "immature",
                 "data_quality": "issues", "minimum_per_arm": 1001}
        for key, value in cases.items():
            with self.subTest(key=key):
                data = valid_input()
                data["design"][key] = value
                interpretation = em.analyze(data)["interpretation"]
                self.assertEqual(interpretation["label"], "descriptive_only")
                self.assertEqual(interpretation["causal_status"], "not_supported")
                self.assertEqual(interpretation["interval_status"], "descriptive_calculation_only")

    def test_unknown_design_declarations_are_not_positive_evidence(self):
        for key in em.DESIGN_ENUMS:
            data = valid_input()
            data["design"][key] = "unknown"
            self.assertEqual(em.analyze(data)["interpretation"]["label"], "descriptive_only")

    def test_synthetic_overrides_good_bad_and_unknown_economics(self):
        for econ in (None, valid_input()["economics"]):
            data = valid_input()
            data["data_kind"], data["economics"] = "synthetic", econ
            self.assertEqual(em.analyze(data)["interpretation"]["label"], "demo_only")
            data["design"]["interference"] = "present"
            self.assertEqual(em.analyze(data)["interpretation"]["label"], "demo_only")

    def test_missing_economics_blocks_commercial_followup(self):
        data = valid_input()
        data["economics"] = None
        result = em.analyze(data)
        self.assertEqual(result["interpretation"]["commercial_status"], "incomplete")
        self.assertEqual(result["interpretation"]["label"], "inconclusive")
        self.assertIsNone(result["economics"])

    def test_positive_conversion_can_have_negative_contribution(self):
        data = valid_input()
        data["economics"]["extra_cost_for_treatment_sample"] = 100000
        self.assertEqual(em.analyze(data)["interpretation"]["label"], "revise_or_stop")

    def test_unequal_allocation_and_normalization(self):
        data = valid_input()
        data["treatment"] = {"n": 2000, "successes": 400}
        data["design"]["expected_treatment_allocation"] = 2 / 3
        result = em.analyze(data)
        self.assertEqual(result["allocation_screen"]["status"], "no_mismatch_detected")
        self.assertAlmostEqual(result["economics"]["implied_incremental_contribution"], 19500)
        self.assertEqual(result["economics"]["basis_treatment_n"], 2000)
        data["design"]["expected_treatment_allocation"] = 0.5
        self.assertEqual(em.analyze(data)["interpretation"]["label"], "descriptive_only")

    def test_small_expected_allocation_cannot_pass_screen(self):
        data = valid_input()
        data["control"] = {"n": 1, "successes": 0}
        data["treatment"] = {"n": 1, "successes": 1}
        data["design"]["minimum_per_arm"] = 1
        result = em.analyze(data)
        self.assertIsNone(result["allocation_screen"]["p_value"])
        self.assertEqual(result["interpretation"]["label"], "descriptive_only")

    def test_unknown_allocation_is_not_inferred_from_equal_arm_sizes(self):
        for assignment in ("randomized", "observational"):
            with self.subTest(assignment=assignment):
                data = valid_input()
                data["design"]["assignment"] = assignment
                data["design"]["expected_treatment_allocation"] = None
                result = em.analyze(data)
                self.assertEqual(result["interpretation"]["label"], "descriptive_only")
                self.assertEqual(result["interpretation"]["causal_status"], "not_supported")
                self.assertEqual(result["allocation_screen"]["status"], "allocation_unknown")
                self.assertIsNone(result["allocation_screen"]["p_value"])
                self.assertIsNone(result["allocation_screen"]["expected_counts"]["treatment"])
                data["data_kind"] = "synthetic"
                self.assertEqual(em.analyze(data)["interpretation"]["label"], "demo_only")

    def test_fixed_or_stratified_allocation_does_not_use_bernoulli_srm_screen(self):
        for model in ("fixed_count", "stratified_or_blocked", "unknown"):
            with self.subTest(model=model):
                data = valid_input()
                data["design"]["allocation_model"] = model
                result = em.analyze(data)
                self.assertEqual(result["allocation_screen"]["status"], "unsupported_allocation_model")
                self.assertIsNone(result["allocation_screen"]["p_value"])
                self.assertEqual(result["interpretation"]["label"], "descriptive_only")

    def test_break_even_is_distinct_from_the_worthwhile_effect(self):
        data = valid_input()
        data["control"] = {"n": 2000, "successes": 100}
        data["treatment"] = {"n": 2000, "successes": 120}
        data["minimum_worthwhile_absolute_lift"] = 0.01
        data["economics"].update(contribution_per_success=40,
                                 extra_cost_for_treatment_sample=1200)
        economics = em.analyze(data)["economics"]
        self.assertAlmostEqual(economics["break_even_absolute_lift"], 0.015)
        self.assertAlmostEqual(economics["implied_incremental_contribution"], -400)
        data["economics"]["contribution_per_success"] = 0
        economics = em.analyze(data)["economics"]
        self.assertIsNone(economics["break_even_absolute_lift"])
        self.assertEqual(economics["implied_incremental_contribution"], -1200)

    def test_invalid_numeric_inputs(self):
        bad_counts = [True, False, 0, -1, 1.0, "100", None, em.MAX_COUNT + 1, float("nan"), float("inf")]
        for value in bad_counts:
            data = valid_input()
            data["control"]["n"] = value
            with self.subTest(value=value), self.assertRaises(em.ValidationError):
                em.analyze(data)
        for value in [-1, True, float("nan"), float("inf"), 1e300]:
            data = valid_input()
            data["economics"]["contribution_per_success"] = value
            with self.subTest(value=value), self.assertRaises(em.ValidationError):
                em.analyze(data)
        data = valid_input()
        data["treatment"]["successes"] = 1001
        with self.assertRaises(em.ValidationError):
            em.analyze(data)

    def test_unrepresentable_break_even_returns_validation_error_json(self):
        data = valid_input()
        data["economics"]["contribution_per_success"] = 1e-310
        with self.assertRaisesRegex(em.ValidationError, "break_even_absolute_lift"):
            em.analyze(data)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", em.__file__, str(source)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stderr, "")
            error = json.loads(result.stdout)["error"]
            self.assertEqual(error["type"], "validation_error")
            self.assertIn("break_even_absolute_lift", error["message"])

    def test_missing_unknown_fields_enums_and_boolean_types(self):
        mutations = [lambda d: d.pop("data_kind"), lambda d: d.update(extra="injected"),
                     lambda d: d["design"].update(assignment="yes"),
                     lambda d: d["design"].update(preregistered=1),
                     lambda d: d.update(schema_version=True),
                     lambda d: d["economics"].update(currency="try")]
        for mutate in mutations:
            data = valid_input()
            mutate(data)
            with self.assertRaises(em.ValidationError):
                em.analyze(data)

    def test_json_never_executes_and_rejects_duplicates_nonfinite(self):
        for text in ('{"n":1,"n":2}', '{"x":{"n":1,"n":2}}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":1e-324}',
                     "__import__('os').system('id')"):
            with self.subTest(text=text), self.assertRaises(em.ValidationError):
                em.parse_json(text)

    def test_cli_json_exit_codes_determinism_and_read_only(self):
        script = Path(em.__file__)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            raw = json.dumps(valid_input()).encode()
            source.write_bytes(raw)
            command = [sys.executable, str(script), str(source)]
            first = subprocess.run(command, capture_output=True, check=False)
            second = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual(first.returncode, 0)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(source.read_bytes(), raw)
            json.loads(first.stdout)
            source.write_text('{"n":1,"n":2}')
            invalid = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual(invalid.returncode, 2)
            self.assertEqual(json.loads(invalid.stdout)["error"]["type"], "validation_error")
            source.write_bytes(b" " * (em.MAX_INPUT_BYTES + 1))
            self.assertEqual(subprocess.run(command, capture_output=True, check=False).returncode, 2)

    def test_numerical_reference_against_scipy_if_available(self):
        try:
            from scipy.stats import binomtest, chi2
        except ImportError:
            self.skipTest("SciPy optional; production has no dependency")
        for k, n in ((0, 1), (1, 1), (0, 100), (20, 100), (35, 100), (999, 1000)):
            reference = binomtest(k, n).proportion_ci(confidence_level=.95, method="wilson")
            actual = em.wilson(k, n)
            self.assertAlmostEqual(actual[0], reference.low, places=13)
            self.assertAlmostEqual(actual[1], reference.high, places=13)
        for c, t, fraction in ((100, 130, .5), (1000, 2000, 2 / 3), (20, 80, .5)):
            result = em.allocation_screen(c, t, fraction, "independent_bernoulli")
            self.assertAlmostEqual(result["p_value"], chi2.sf(result["statistic"], 1), places=13)
        t_ci, c_ci = binomtest(35, 100).proportion_ci(method="wilson"), binomtest(20, 100).proportion_ci(method="wilson")
        reference = [.15 - math.sqrt((.35 - t_ci.low)**2 + (c_ci.high - .20)**2),
                     .15 + math.sqrt((t_ci.high - .35)**2 + (.20 - c_ci.low)**2)]
        for actual, expected in zip(em.newcombe(35, 100, 20, 100), reference):
            self.assertAlmostEqual(actual, expected, places=13)

    def test_cli_accepts_utf8_bom_and_rejects_utf16(self):
        raw = json.dumps(valid_input()).encode("utf-8")
        cases = ((b"\xef\xbb\xbf" + raw, 0),
                 (raw.decode("utf-8").encode("utf-16"), 2))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input with spaces.json"
            for payload, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    source.write_bytes(payload)
                    result = subprocess.run([sys.executable, "-B", em.__file__, str(source)],
                                            capture_output=True, text=True, check=False)
                    self.assertEqual(result.returncode, expected_code)
                    self.assertEqual(result.stderr, "")
                    parsed = json.loads(result.stdout)
                    if expected_code == 0:
                        self.assertEqual(parsed["interpretation"]["label"], "supports_bounded_followup")
                    else:
                        self.assertEqual(parsed["error"]["type"], "validation_error")
                    self.assertEqual(source.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
