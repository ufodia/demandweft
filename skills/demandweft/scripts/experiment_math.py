#!/usr/bin/env python3
"""Offline two-arm Bernoulli analysis; declarations are never treated as audited facts."""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from statistics import NormalDist

MAX_COUNT = 1_000_000_000
MAX_MONEY = 1_000_000_000_000
MAX_INPUT_BYTES = 65_536
Z = NormalDist().inv_cdf(0.975)
SRM_ALPHA = 0.001  # A documented screening policy, not an effect-test alpha.
TOP_KEYS = {
    "schema_version", "data_kind", "control", "treatment", "design",
    "minimum_worthwhile_absolute_lift", "economics",
}
DESIGN_ENUMS = {
    "assignment": ("randomized", "observational", "unknown"),
    "allocation_model": ("independent_bernoulli", "fixed_count", "stratified_or_blocked", "unknown"),
    "unit": ("person", "cluster", "unknown"),
    "independence": ("independent", "dependent", "unknown"),
    "interference": ("absent", "present", "unknown"),
    "horizon_status": ("complete", "incomplete", "unknown"),
    "outcome_maturity": ("mature", "immature", "unknown"),
    "data_quality": ("clear", "issues", "unknown"),
}
DESIGN_KEYS = set(DESIGN_ENUMS) | {
    "preregistered", "fixed_horizon", "minimum_per_arm",
    "expected_treatment_allocation",
}


class ValidationError(ValueError):
    """An input cannot be interpreted under the declared schema."""


def object_keys(value, expected, path):
    if type(value) is not dict:
        raise ValidationError(f"{path} must be an object")
    missing, extra = expected - value.keys(), value.keys() - expected
    if missing or extra:
        raise ValidationError(
            f"{path}: missing keys {sorted(missing)}; unknown keys {sorted(extra)}"
        )


def integer(value, low, high, path):
    if type(value) is not int or not low <= value <= high:
        raise ValidationError(f"{path} must be an integer in [{low}, {high}]")


def number(value, low, high, path):
    if (type(value) not in (int, float) or not low <= value <= high
            or not math.isfinite(value)):
        raise ValidationError(f"{path} must be a finite number in [{low}, {high}]")


def enum(value, choices, path):
    if type(value) is not str or value not in choices:
        raise ValidationError(f"{path} must be one of {', '.join(choices)}")


def validate(data):
    object_keys(data, TOP_KEYS, "input")
    integer(data["schema_version"], 1, 1, "schema_version")
    enum(data["data_kind"], ("observed", "synthetic"), "data_kind")
    for name in ("control", "treatment"):
        arm = data[name]
        object_keys(arm, {"n", "successes"}, name)
        integer(arm["n"], 1, MAX_COUNT, f"{name}.n")
        integer(arm["successes"], 0, arm["n"], f"{name}.successes")
    design = data["design"]
    object_keys(design, DESIGN_KEYS, "design")
    for key, choices in DESIGN_ENUMS.items():
        enum(design[key], choices, f"design.{key}")
    for key in ("preregistered", "fixed_horizon"):
        if type(design[key]) is not bool:
            raise ValidationError(f"design.{key} must be a JSON boolean")
    integer(design["minimum_per_arm"], 1, MAX_COUNT, "design.minimum_per_arm")
    if design["expected_treatment_allocation"] is not None:
        number(design["expected_treatment_allocation"], 0.000001, 0.999999,
               "design.expected_treatment_allocation")
    number(data["minimum_worthwhile_absolute_lift"], 0, 1,
           "minimum_worthwhile_absolute_lift")
    econ = data["economics"]
    if econ is not None:
        object_keys(econ, {"currency", "contribution_per_success",
                          "extra_cost_for_treatment_sample"}, "economics")
        if type(econ["currency"]) is not str or not re.fullmatch(r"[A-Z]{3}", econ["currency"]):
            raise ValidationError("economics.currency must be three uppercase ASCII letters")
        for key in ("contribution_per_success", "extra_cost_for_treatment_sample"):
            number(econ[key], 0, MAX_MONEY, f"economics.{key}")


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(_value):
    raise ValidationError("NaN and Infinity are not permitted")


def parse_float(value):
    parsed = float(value)
    coefficient = value.lower().partition("e")[0]
    underflowed_nonzero = parsed == 0.0 and any(ch in "123456789" for ch in coefficient)
    if not math.isfinite(parsed) or underflowed_nonzero:
        raise ValidationError("number is outside the supported finite floating-point range")
    return parsed


def parse_json(text):
    try:
        return json.loads(text, object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant, parse_float=parse_float)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValidationError("invalid JSON or excessive nesting") from exc


def wilson(successes, n):
    """Two-sided 95% Wilson score limits, without continuity correction."""
    p, z2 = successes / n, Z * Z
    denominator = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denominator
    radius = Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominator
    # Preserve the exact boundary limits despite floating-point cancellation.
    return [0.0 if successes == 0 else max(0.0, center - radius),
            1.0 if successes == n else min(1.0, center + radius)]


def newcombe(t_successes, t_n, c_successes, c_n):
    """Independent-sample Newcombe Wilson combination: treatment minus control.

    Formula matches statsmodels confint_proportions_2indep(method='newcomb',
    compare='diff', alpha=.05). No paired-data or sequential correction.
    """
    pt, pc = t_successes / t_n, c_successes / c_n
    lt, ut = wilson(t_successes, t_n)
    lc, uc = wilson(c_successes, c_n)
    difference = pt - pc
    return [max(-1.0, difference - math.hypot(pt - lt, uc - pc)),
            min(1.0, difference + math.hypot(ut - pt, pc - lc))]


def allocation_screen(c_n, t_n, expected_fraction, allocation_model):
    if expected_fraction is None:
        return {"method": "pearson_chi_square_df1", "alpha": SRM_ALPHA,
                "expected_treatment_allocation": None,
                "expected_counts": {"control": None, "treatment": None},
                "statistic": None, "p_value": None, "status": "allocation_unknown"}
    if allocation_model != "independent_bernoulli":
        return {"method": "not_applicable", "alpha": SRM_ALPHA,
                "expected_treatment_allocation": expected_fraction,
                "expected_counts": {"control": None, "treatment": None},
                "statistic": None, "p_value": None,
                "status": "unsupported_allocation_model"}
    total = c_n + t_n
    expected_t = total * expected_fraction
    expected_c = total * (1 - expected_fraction)
    adequate = min(expected_c, expected_t) >= 5
    statistic = (t_n - expected_t) ** 2 / expected_t + (c_n - expected_c) ** 2 / expected_c
    p_value = math.erfc(math.sqrt(statistic / 2)) if adequate else None
    status = ("insufficient_expected_counts" if not adequate else
              "mismatch_detected" if p_value < SRM_ALPHA else "no_mismatch_detected")
    return {"method": "pearson_chi_square_df1", "alpha": SRM_ALPHA,
            "expected_treatment_allocation": expected_fraction,
            "expected_counts": {"control": expected_c, "treatment": expected_t},
            "statistic": statistic, "p_value": p_value, "status": status}


def blocking_reasons(data, allocation):
    design = data["design"]
    requirements = {
        "assignment": "randomized", "unit": "person",
        "independence": "independent", "interference": "absent",
        "horizon_status": "complete", "outcome_maturity": "mature",
        "data_quality": "clear", "preregistered": True, "fixed_horizon": True,
    }
    reasons = [f"design.{key}_requirement_not_met" for key, needed in requirements.items()
               if design[key] != needed]
    if min(data["control"]["n"], data["treatment"]["n"]) < design["minimum_per_arm"]:
        reasons.append("planned_minimum_per_arm_not_reached")
    if allocation["status"] != "no_mismatch_detected":
        status = allocation["status"]
        reasons.append(status if status.startswith("allocation_") else "allocation_" + status)
    return reasons


def analyze(data):
    """Return a fresh report; never mutate the supplied object or input file."""
    validate(data)
    c, t = data["control"], data["treatment"]
    pc, pt = c["successes"] / c["n"], t["successes"] / t["n"]
    difference = pt - pc
    interval = newcombe(t["successes"], t["n"], c["successes"], c["n"])
    allocation = allocation_screen(c["n"], t["n"],
                                   data["design"]["expected_treatment_allocation"],
                                   data["design"]["allocation_model"])
    blockers = blocking_reasons(data, allocation)
    synthetic = data["data_kind"] == "synthetic"
    eligible = not synthetic and not blockers
    econ = data["economics"]
    economics = None
    if econ is not None:
        scale = t["n"] * econ["contribution_per_success"]
        cost = econ["extra_cost_for_treatment_sample"]
        break_even = cost / scale if scale > 0 else None
        if break_even is not None and not math.isfinite(break_even):
            raise ValidationError(
                "economics.break_even_absolute_lift exceeds the finite numeric range; "
                "the positive contribution_per_success is too small relative to cost"
            )
        economics = {
            "currency": econ["currency"], "basis_treatment_n": t["n"],
            "contribution_per_success": econ["contribution_per_success"],
            "extra_cost_for_treatment_sample": cost,
            "break_even_absolute_lift": break_even,
            "implied_incremental_contribution": difference * scale - cost,
            "implied_incremental_contribution_interval_95": [x * scale - cost for x in interval],
            "margin_and_cost_assumed_fixed": True,
        }
    decision_reasons = []
    commercial = "incomplete" if econ is None else "not_inferentially_eligible"
    if synthetic:
        label = "demo_only"
        decision_reasons.append("synthetic_data_cannot_support_a_business_claim")
    elif not eligible:
        label = "descriptive_only"
        decision_reasons.append("design_or_quality_requirements_not_met")
    elif economics is None:
        label = "inconclusive"
        decision_reasons.append("economics_missing_commercial_decision_incomplete")
    else:
        minimum = data["minimum_worthwhile_absolute_lift"]
        net_low, net_high = economics["implied_incremental_contribution_interval_95"]
        if interval[0] > minimum and net_low > 0:
            label, commercial = "supports_bounded_followup", "conditional_support"
            decision_reasons.append("lower_bounds_exceed_worthwhile_lift_and_zero_contribution")
        elif interval[1] < minimum or net_high <= 0:
            label, commercial = "revise_or_stop", "conditional_unfavorable"
            decision_reasons.append("upper_bound_below_worthwhile_lift_or_not_positive_contribution")
        else:
            label, commercial = "inconclusive", "uncertain"
            decision_reasons.append("intervals_do_not_resolve_the_declared_decision_thresholds")
    return {
        "schema_version": 1, "data_kind": data["data_kind"],
        "method": {"confidence_level": 0.95, "arm_interval": "wilson",
                   "difference_interval": "newcombe_independent_wilson",
                   "continuity_correction": False},
        "rates": {name: {"n": arm["n"], "successes": arm["successes"],
                          "estimate": arm["successes"] / arm["n"],
                          "interval_95": wilson(arm["successes"], arm["n"])}
                  for name, arm in (("control", c), ("treatment", t))},
        "comparison": {"direction": "treatment_minus_control", "absolute_lift": difference,
                       "relative_lift": None if pc == 0 else difference / pc,
                       "interval_95": interval,
                       "minimum_worthwhile_absolute_lift": data["minimum_worthwhile_absolute_lift"]},
        "allocation_screen": allocation, "economics": economics,
        "interpretation": {
            "label": label, "conditions_met": eligible,
            "causal_status": "conditional_on_declared_assumptions" if eligible else "not_supported",
            "interval_status": "approximate_fixed_horizon" if eligible else "descriptive_calculation_only",
            "commercial_status": commercial, "blocking_reasons": blockers,
            "decision_reasons": decision_reasons, "assumptions": "declared_not_audited",
            "automatic_action": "none",
        },
        "limitations": [
            "Declarations are not audited; equivalent definitions and eligibility in both arms require separate verification.",
            "One predeclared binary outcome per independently assigned person; counts must include all eligible assigned people.",
            "Wilson/Newcombe intervals have approximate coverage, not a probability that an effect is in the reported interval.",
            "No correction for repeated looks, selected outcomes, multiple comparisons, clustering, dependence, or interference.",
            "Descriptive/demo intervals are arithmetic under a working model, not calibrated inferential evidence for that design.",
            "A passed allocation screen does not prove valid randomization or exclude missingness and measurement bias.",
            "Contribution calculations assume a common fixed contribution per success and known incremental costs at treatment sample size.",
            "Cost/margin uncertainty, refunds, long-term effects, and transport to other audiences are not estimated.",
            "The calculator does not evaluate experiment guardrails; apply the recorded stopping conditions before acting on this label.",
            "No label authorizes publishing, spending, scaling, or a causal or commercial guarantee.",
        ],
    }


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) != 1:
            raise ValidationError("usage: python3 experiment_math.py INPUT.json")
        path = Path(args[0])
        if not path.is_file():
            raise ValidationError("input must be an existing regular file")
        with path.open("rb") as source:
            raw = source.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValidationError(f"input exceeds {MAX_INPUT_BYTES} bytes")
        report = analyze(parse_json(raw.decode("utf-8-sig")))
        output = json.dumps(report, allow_nan=False, sort_keys=True, indent=2)
    except (OSError, UnicodeError, ValueError, RecursionError, OverflowError) as exc:
        print(json.dumps({"error": {"type": "validation_error", "message": str(exc)}}, allow_nan=False))
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
