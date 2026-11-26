# Experiment arithmetic and decision boundaries

Run `python3 scripts/experiment_math.py /absolute/path/input.json` from the skill directory. On Windows with the Python launcher, use `py -3 scripts/experiment_math.py "C:\path with spaces\input.json"`. Python 3.9+ and the standard library are sufficient. The command reads one local UTF-8 JSON file (an optional leading UTF-8 BOM is accepted), performs no networking, changes no input, and prints deterministic JSON. Other encodings, including UTF-16, are rejected. Exit `0` means the input was analyzed, including inconclusive, blocked, or synthetic results. Exit `2` means validation failed; stdout still contains a JSON error. The tool never publishes, purchases, changes a campaign, or spends money.

## Input contract, version 1

Every field below is required. `economics: null` explicitly means unknown economics. Set `expected_treatment_allocation: null` when no predeclared allocation is known; equal observed arm sizes do not establish an allocation plan. There are no implicit defaults. Unknown keys and duplicate JSON keys are rejected at every object level.

```json
{
  "schema_version": 1,
  "data_kind": "synthetic",
  "control": {"n": 1000, "successes": 100},
  "treatment": {"n": 1000, "successes": 200},
  "design": {
    "assignment": "randomized",
    "allocation_model": "independent_bernoulli",
    "unit": "person",
    "independence": "independent",
    "interference": "absent",
    "preregistered": true,
    "fixed_horizon": true,
    "horizon_status": "complete",
    "outcome_maturity": "mature",
    "data_quality": "clear",
    "minimum_per_arm": 1000,
    "expected_treatment_allocation": 0.5
  },
  "minimum_worthwhile_absolute_lift": 0.02,
  "economics": {
    "currency": "TRY",
    "contribution_per_success": 100,
    "extra_cost_for_treatment_sample": 500
  }
}
```

This example is invented and always returns `demo_only`. Never relabel a simulated or illustrative dataset `observed`. A real dataset needs traceable source evidence outside this calculator.

| Field | Accepted values and meaning |
| --- | --- |
| `data_kind` | `observed`, `synthetic` |
| `n` | Integer from 1 to 1,000,000,000; unique eligible units in that arm, not impressions, sessions, or observations after outcome-dependent filtering; inferential labels require independently assigned people |
| `successes` | Integer from 0 to that arm's `n`; each person contributes at most one success under the same outcome and observation window |
| `assignment` | `randomized`, `observational`, `unknown` |
| `allocation_model` | `independent_bernoulli`, `fixed_count`, `stratified_or_blocked`, `unknown`; the Pearson sample-ratio screen is supported only for independent Bernoulli assignment with a predeclared treatment fraction; all other models block inferential labels until reviewed with a design-appropriate diagnostic |
| `unit` | `person`, `cluster`, `unknown` |
| `independence` | `independent`, `dependent`, `unknown` |
| `interference` | `absent`, `present`, `unknown`; contamination, spillover, and cross-arm sharing can violate this |
| `preregistered`, `fixed_horizon` | JSON booleans; `true` asserts the outcome, worthwhile effect, sample plan, allocation, economics, and decision rule were fixed before observing results, and the original stopping rule was followed |
| `horizon_status` | `complete`, `incomplete`, `unknown`; reaching a sample minimum alone does not complete an observation window |
| `outcome_maturity` | `mature`, `immature`, `unknown`; all included people have completed the declared outcome window |
| `data_quality` | `clear`, `issues`, `unknown`; separately inspect missing outcomes, exclusions, tracking failures, duplicated people, bots, and inconsistent definitions |
| `minimum_per_arm` | Integer from 1 to 1,000,000,000, specified by the experiment's plan; the calculator does not invent a sector threshold or perform power planning |
| `expected_treatment_allocation` | Predeclared treatment fraction, from 0.000001 to 0.999999, or `null` when unknown; use the planned fraction, never infer it from the observed fraction. Unknown allocation blocks inferential labels |
| `minimum_worthwhile_absolute_lift` | From 0 to 1; `0.02` means two percentage points, not a 2% relative increase; more successes must be beneficial |
| `contribution_per_success` | Fixed common contribution per success, after relevant variable costs, from 0 to 1,000,000,000,000; revenue alone is insufficient |
| `extra_cost_for_treatment_sample` | Additional cost of treatment versus serving the same `n_treatment` people under control, in the same currency and observation window; nonnegative and at most 1,000,000,000,000 |
| `currency` | Three uppercase ASCII letters; syntax is checked, exchange rates and currency validity are not |

Numeric inputs reject booleans, strings, NaN, infinities, underflowed nonzero decimals and out-of-range values. Only `economics` and `expected_treatment_allocation` accept `null`. Counts reject floating-point values, even `100.0`. The file limit is 65,536 bytes. Negative-margin outcomes, varying contribution by arm, cost savings expressed as negative extra costs, revenue distributions, repeated events, paired observations, and clustered designs require another analysis; do not force them into this schema.

## Calculation

Each arm receives a two-sided approximate 95% Wilson score interval without continuity correction. The difference is **treatment minus control**. Its approximate 95% interval combines the two Wilson intervals using the independent-sample Newcombe method, matching the method named `newcomb` in the [official statsmodels independent-proportion documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html) and [implementation](https://www.statsmodels.org/stable/_modules/statsmodels/stats/proportion.html). With rates `p_t`, `p_c` and Wilson limits `(l_t, u_t)`, `(l_c, u_c)`, the limits are:

- Lower: `(p_t - p_c) - sqrt((p_t - l_t)^2 + (u_c - p_c)^2)`.
- Upper: `(p_t - p_c) + sqrt((u_t - p_t)^2 + (p_c - l_c)^2)`.

Relative lift is `(p_t - p_c) / p_c` and is `null` when the observed control rate is zero. No relative-lift interval is claimed. An absolute lift of `0.1` means ten percentage points; a relative lift of `1.0` means 100%.

The sample-ratio screen uses Pearson's chi-squared goodness-of-fit statistic with one degree of freedom, comparing observed arm sizes with the declared allocation **only for independent Bernoulli assignment**. Fixed-count allocation makes the total assignment count predetermined, while blocked or stratified allocation needs a design-matched check; for those models the helper reports `unsupported_allocation_model`, gives no p-value, and blocks inferential labels. When supported, a p-value below **0.001** blocks decision labels; this threshold is this tool's fixed policy, not a universal scientific standard. Both expected counts must be at least five; otherwise the approximation is not used to clear the screen. The screen concerns assignment/collection quality, not treatment effectiveness. [Microsoft Research explains SRM detection and why apparent treatment effects must not be trusted before a mismatch is investigated](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/). Passing this screen cannot prove randomization or data quality.

For known economics, implied incremental contribution for the **treatment sample size** is `n_treatment * absolute_lift * contribution_per_success - extra_cost_for_treatment_sample`. Apply the same linear transformation to the difference interval. This is not a comparison of raw revenue totals in unequal arms and is not a profit forecast. Its interval incorporates conversion uncertainty only, assuming the supplied common contribution and extra costs are fixed and correct. Margin, cost, refund, lifetime-value and transport uncertainty remain unmodeled. If these inputs are not justified, use `economics: null`.

The economic break-even absolute lift is `extra_cost_for_treatment_sample / (n_treatment * contribution_per_success)`. The output reports it separately from the predeclared worthwhile effect: clearing a user-selected effect threshold need not cover costs. It returns `null` when contribution per success is zero, because no unique break-even lift exists under that model. An extremely small positive contribution can make this ratio exceed the finite numeric range. Such inputs are rejected with a JSON validation error and exit code `2`; no break-even estimate is emitted. This arithmetic does not change the predeclared success rule after seeing results.

When the planned allocation is unknown, the screen returns `allocation_unknown` with null expected counts and p-value. It never substitutes the observed arm ratio, and the result remains descriptive or demo-only. For a known but unsupported allocation model, it returns `unsupported_allocation_model`, also with no p-value.

## Labels and interpretation

Conditions for an inferential label are all declared: observed data, random assignment, independent person units, no interference, preregistration, fixed and completed horizon, mature outcomes, clear data quality, both planned minimum samples reached, and a passed allocation screen. These are **declared, not audited**. Equivalent eligibility, event definitions and observation windows must be verified separately; a large sample cannot repair a broken design.

| Label | Meaning |
| --- | --- |
| `demo_only` | Any synthetic input, regardless of apparent effects or other settings; no business or causal claim |
| `descriptive_only` | Any unmet design, maturity, quality, minimum-sample or allocation condition; the interval is only an arithmetic working-model comparison and is not calibrated evidence for the actual design |
| `inconclusive` | Eligible design but missing economics, or intervals do not resolve the declared decision thresholds; missing economics also sets `commercial_status` to `incomplete` |
| `supports_bounded_followup` | Eligible design and known economics; difference interval lower bound strictly exceeds the worthwhile absolute lift and contribution interval lower bound strictly exceeds zero |
| `revise_or_stop` | Eligible design and known economics; difference interval upper bound is below the worthwhile lift, or contribution interval upper bound is at most zero |

The output's qualified `causal_status` is `conditional_on_declared_assumptions` only when all design conditions pass. This is not an independent causal audit. A bounded follow-up label is a recommendation for a separately planned limited next experiment; it does not authorize rollout or spending. Multiple metrics, selected subgroups, repeated looks, optional stopping, network effects and clusters need appropriate designs and adjusted methods. Changing the horizon or minimum after seeing a result invalidates the declarations; do not simply add people until this command prints a preferred label. Approximate 95% confidence intervals do not assign a 95% probability to this specific effect being inside the reported range.

The helper has no inputs for guardrails, customer usefulness, or recipient outcomes. An arithmetic recommendation covers the primary outcome and supplied economics only. Apply the recorded guardrails and evaluate their evidence before deciding whether to follow up.

## Verification

Run `python3 -B -m unittest discover -s scripts -p 'test_experiment_math.py' -v`. Tests cover numerical boundaries (including exact zero- and all-success endpoints at the maximum count), unrepresentable break-even ratios, zero events, sign reversal, unequal allocation and contribution normalization, missing economics, synthetic precedence, design failures, malformed/duplicate JSON, input immutability and deterministic CLI exit behavior. If SciPy is already installed, an optional offline cross-check compares Wilson limits and SRM p-values with its independent implementation. SciPy is not required for production use and is never installed by this tool.
