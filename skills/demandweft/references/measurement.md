# Measure usefulness, business value, and propagation

## Three questions, three records

| Question | Useful observations | Does not establish |
| --- | --- | --- |
| Did the experience help? | Promised task completed, a constraint resolved, a correct non-fit identified, contextual participant feedback. | Revenue, willingness to pay, causal business impact. |
| Did the business benefit? | Qualified attended appointment, activated account, paid order, retention, contribution after variable costs. | Customer benefit if the experience misled or pressured people. |
| Did another person benefit? | Distinct recipients completing their own task; later re-sharing within a declared window. | Incrementality, profitability, universal virality, or customers from share clicks. |

Define denominators. People, sessions, invitations, opens, tasks, and orders are not interchangeable. Preserve raw counts, windows, missing events, and deduplication limits.

## Before a pilot

Record the experience/offer version, audience, channel, hypothesis, one primary outcome, unit, eligibility, exclusions, follow-up window, comparison, and assignment method. State the smallest worthwhile improvement, planned sample or horizon, slow-outcome handling, guardrails, budget, and the rules for follow-up, revise/stop, and inconclusive results.

Do not choose a new primary outcome after observing an unfavorable result. Treat material changes as a new version. Preserve negative and inconclusive evidence.

Define what triggers each guardrail, where and when it will be observed, and what to do if its data are missing. Identify stopping conditions separately from signals that only call for investigation.

## Match the method

- **Demonstration:** verify function using fixtures or agent walkthroughs. Do not call synthetic participants real customers.
- **Qualitative exploration:** use actual participant statements and behavior. State selection and sample; do not forecast population conversion.
- **Observational pilot:** report what happened and possible confounding. Before/after, channels, and self-selected tool users do not automatically identify an incremental effect.
- **Randomized comparison:** preserve assignment and count eligible assigned units consistently. Wait for the declared horizon and outcome maturity; investigate quality first.
- **Referral/coordination:** anticipate interference. Use appropriate cluster/network analysis; the independent-proportion helper does not support it.

A handful of interviews can refine a buying question but cannot support a precise lift claim. A useful inexpensive asset may reasonably remain while evidence accumulates.

## Economics

Use contribution per defined success, not gross revenue or speculative lifetime value. Include relevant variable fulfillment, discounts, refunds, paid API calls, and support work. Label assumptions and unknown costs.

For a two-arm comparison normalized to the treatment sample:

`additional_successes = treatment_n × (treatment_rate − control_rate)`

`incremental_contribution = additional_successes × contribution_per_success − extra_cost_for_treatment_sample`

`break_even_absolute_lift = extra_cost_for_treatment_sample / (treatment_n × contribution_per_success)`

These are scenarios when design or economic assumptions are unverified, not monthly forecasts. Unknown contribution makes a commercial decision incomplete.

Keep time and capacity visible even without a monetary hourly rate. Separate existing fixed costs, incremental operating costs, and one-time implementation costs. State the future rollout horizon to prevent ignoring or double-counting costs.

## Numerical helper scope

Read [experiment-math.md](experiment-math.md) for the actual schema. The helper calculates descriptive rates and approximate independent-binomial intervals, an optional economic scenario, and conditional readiness checks.

Do not apply it as a valid causal analysis to clusters, repeated actions treated as people, fractional counts, continuous revenue, selected multi-arm winners, or repeatedly monitored fixed-horizon results. A declared randomization field is not proof of randomization; inspect actual logs or records.

Report counts and absolute percentage points. Relative change is undefined at a zero baseline. Retain uncertainty rather than replacing it with dramatic percentages.

## Propagation

Use cohorts and finite observation windows. Observe recipient utility before optimizing sharing. Avoid counting self-visits or repeated opens as new people where legitimately distinguishable.

A new-recipient/original-participant ratio is a scoped descriptive ratio. Do not multiply guessed rates into a claimed viral coefficient or extrapolate an early chain into perpetual growth. Shared groups can violate simple A/B independence.

## Decision language

Recover the plan for the tested version. Compare each guardrail with its own evidence before combining results into a recommendation. If a stopping condition was met, follow the planned stop action even when the primary outcome improved. If an essential guardrail is unmeasured or its observation window is incomplete, keep the decision inconclusive unless an independently verified stopping condition already applies. Report the business finding and the guardrail outcome separately.

- Label fabricated fixtures synthetic even when arithmetic is correct.
- Label observational comparisons associations.
- Use inconclusive when evidence cannot support the predeclared decision.
- Use supports a bounded follow-up under stated assumptions for qualifying results.
- Retain unfavorable usefulness, wrong-fit lead, cost, and capacity results alongside conversions.
- Keep three outcome records; do not average them into a proprietary growth score.

## Primary methods

- [Statsmodels: intervals for two independent proportions](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html).
- [Microsoft Research: Diagnosing Sample Ratio Mismatch](https://www.microsoft.com/en-us/research/publication/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments-a-taxonomy-and-rules-of-thumb-for-practitioners/).

Consult authoritative methodology for unsupported designs. Method documentation does not validate a campaign's observations or implementation.
