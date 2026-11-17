# Demandweft contract schema, version 1

## Contents

- [Purpose and boundaries](#purpose-and-boundaries)
- [Result and exit codes](#result-and-exit-codes)
- [Top-level fields](#top-level-fields)
- [Evidence](#evidence)
- [Buyer and experience](#buyer-and-experience)
- [Claims and public use](#claims-and-public-use)
- [Propagation, success, and budget](#propagation-success-and-budget)
- [Example](#example)

## Purpose and boundaries

Use one JSON contract for one buyer decision and one concrete proof experience.
Run `python3 scripts/validate_contract.py PATH_TO_CONTRACT.json` from the skill
directory. The validator reads only the named JSON file and writes its result to
stdout. It does not open sources, execute their contents, write files, contact
services, publish, or spend. Python 3.9+ and its standard library are sufficient.

The check establishes structural completeness and reference consistency. It
cannot establish truth, customer demand, causal effect, permissions, or that an
experience actually works. Classifying a source as `observed` is a declaration,
not an observation made by this script. `ready_for_review` always requires human
or agent review of the underlying material and separate action authorization.

## Result and exit codes

| Exit | Output status | Meaning |
| --- | --- | --- |
| `0` | `ready_for_review` | Required structure is present and no structural blocking rule failed. Review the evidence and deliverable. |
| `1` | `draft` | Incomplete required fields without a blocking error, an explicitly draft contract, a planned experience, or an unclassified comparison. |
| `2` | `invalid` | Invalid JSON/type/value, a missing contract ID or schema version, unresolved or duplicate IDs, or a contradictory/blocking declaration. |

Every output includes `errors`, `incomplete`, `caveat`, and `manual_checks`.
Blocking errors take precedence over incomplete fields. Missing contract `id`
or `schema_version` is invalid because these identify the contract and its rules.
Other missing fields can still leave a blocking declaration: for example,
illustrative public claims without the required demo flags, or a propagation
outcome without an enabled mode. A missing budget alone is a draft, never an
implicit unlimited budget. Invalid input and CLI usage also produce JSON on
stdout. Input is limited to 2 MiB of UTF-8 JSON, including an optional leading
UTF-8 byte-order mark (BOM). Other encodings are not accepted.

## Top-level fields

All fields below are required. Unknown fields are rejected to catch misspellings
and accidental approval flags. Optional fields are stated explicitly below.

| Field | Type / allowed values |
| --- | --- |
| `schema_version` | Integer `1`; `true`, `1.0`, and `"1"` are invalid. |
| `id` | String ID. |
| `status` | `draft` or `ready_for_review`. This is a review state, never permission. |
| `demo_only` | Boolean. If true, `explicitly_demo` must also be true. |
| `explicitly_demo` | Boolean; declare that illustrative material is visibly identified as a demonstration. The actual labeling needs manual review. |
| `evidence` | Array of evidence records; an empty array is possible only without supported claims or buyer/verification assertions. |
| `buyer` | Buyer object below. |
| `experience` | Experience object below. |
| `claims` | Array of exact claim records. |
| `public` | Object containing `claim_ids`, an array of claim IDs. |
| `propagation` | Propagation object below. |
| `success` | Separate success definitions below. |
| `budget` | Budget object below. |

IDs use 1–64 lowercase letters, digits, underscores or hyphens and start with a
letter. Evidence IDs are unique within evidence; claim IDs are unique within
claims. Every referenced ID must resolve, and reference arrays cannot repeat an
ID. Required strings must contain non-whitespace text. Missing, null, or blank
required text and missing or null objects count as incomplete, subject to the
blocking rules above. Null arrays, booleans, and numbers are invalid; other wrong
types are invalid. Omit unused optional fields. Duplicate JSON object keys and
non-finite numbers are rejected everywhere, including nested objects. Numeric
fields never accept bools.

## Evidence

Each record contains `id`, `type`, `kind`, `source`, `scope`, and `summary`.
`source`, `scope`, and `summary` are nonempty strings. Use an exact file/section,
URL, recording timestamp, supplied-document reference, or experiment record for
`source`; the validator does not resolve or fetch it.

- `type`: `observed`, `user_provided`, `inferred`, or `synthetic`.
- `kind`: `customer`, `implementation`, `demonstration`, `measurement`,
  `testimonial`, or `reference`.
- Optional `independent`: Boolean. `true` is allowed only for `measurement`.
  It asserts that the measurement is separate from illustrative/demo outputs and
  the claim-generating exercise. Review study design and provenance; this flag
  does not mean independent third-party certification or prove causality.

`observed` and `user_provided` count as actual evidence types for structural
checks. Generated personas, imagined quotes, forecast lifts, and fictional data
must be `synthetic` or `inferred`, never relabeled to satisfy the validator.

## Buyer and experience

`buyer` requires `segment`, `decision_question`, `barrier`, `status`, and
`evidence_ids`. Status is `hypothesis` or `supported`. Supported buyer
understanding needs at least one referenced actual `customer` record. Without
that evidence, explicitly retain `hypothesis`; simulation does not establish
market demand.

`experience` requires `deliverable`, `personal_utility`, `non_fit_outcome`,
`implementation_state`, and `verification_evidence_ids`.

- Describe a concrete usable artifact in `deliverable`: inline text, a located
  guide, a concierge workflow, a form, or a working application can qualify.
- State the intended user benefit in `personal_utility` without inventing results.
- Provide a useful, honest alternative or exit in `non_fit_outcome`.
- State is `planned`, `built`, or `verified`. Planned always remains draft.
  Built asserts the artifact exists, not that efficacy was measured.
- Verified needs actual `implementation` or `demonstration` evidence. Manual
  review must confirm that it covers the specified artifact and behavior.

## Claims and public use

Every claim requires `id`, exact `text`, `category`, `status`, and `evidence_ids`.
Categories are `capability`, `descriptive_outcome`, `causal_outcome`, `comparison`,
and `testimonial`. Status is `supported`, `hypothesis`, or `illustrative`.

| Supported category | Structural evidence requirement |
| --- | --- |
| `capability` | Actual implementation or demonstration evidence; experience cannot be merely planned. |
| `descriptive_outcome` | Actual measurement evidence. Demonstrating a feature does not measure conversion, retention, sales, or other results. |
| `causal_outcome` | Actual measurement with `independent: true`; causal design and attribution still require manual review. |
| `comparison` | Set optional `comparison_basis` to `features` or `performance`. A supported comparison without this classification remains draft. Features accept actual reference, implementation, demonstration, or measurement evidence; performance requires actual measurement. |
| `testimonial` | Actual testimonial evidence; original wording, identity/attribution and usage permission need manual review. |

`comparison_basis` is forbidden for other categories even when null or blank;
omit the field entirely. A factual feature matrix
can use current product documentation; claims of better speed, revenue, or
effectiveness require measurement and the appropriate scope. The script does
not infer the category from prose. Deliberately labeling an outcome as a
capability can evade a structural check and must be caught in manual review.

Illustrative claims require `explicitly_demo: true`. `public.claim_ids` may refer
only to supported claims, with one exception: a `demo_only: true` and
`explicitly_demo: true` bundle can include illustrative claims. Hypotheses cannot
be placed in the public claim list. Demo flags never make synthetic evidence
support a real outcome. Review all public copy: the list cannot detect unlisted
claims, implied promises, context removed from quotations, or misleading labels.

## Propagation, success, and budget

`propagation` requires `mode` and `forced_sharing`. Modes are `none`, `adapt`,
`coordinate`, and `challenge`. `forced_sharing` must be false. When enabled,
require nonempty `recipient_value`, `sender_value`, and `privacy_scope`.
Sharing must not gate the useful personal outcome. Those declarations do not
prove the UI behaves accordingly; inspect it. Mode `none` is a complete option.

`success` requires `user_value` and `business_outcome`. Add
`propagation_outcome` only when propagation is enabled; then it is required.
Each contains `metric` and `success_definition`, both nonempty strings. Names
and definitions must differ across the outcomes, after whitespace/case
normalization. This only catches literal reuse: manually check semantic overlap,
denominators, observation windows, and that a share/click is not presented as
recipient benefit or a sale. Definitions are plans, not achieved results.

`budget` requires `currency`, `max_cash`, and `max_hours`. Currency has three
uppercase letters; verify it is the intended valid currency separately. Numbers
must be finite and nonnegative. Zero is a valid cap. A budget is a limit, not
authorization to spend it. Missing values remain draft.

## Example

`assets/contract.example.json` is wholly fictional and contains no private user
data or real customer results. Its inline worksheet is a completed text
demonstration, so `built` is accurate for that text only. It does not assert that
the fictional product is implemented. Its buyer understanding remains a
hypothesis; its sole public claim is visibly illustrative. The success definitions
describe a future pilot. A passing lint is a schema example, not validated demand.
