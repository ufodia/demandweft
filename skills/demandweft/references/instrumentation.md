# Observe the customer's job and the business outcome

Read this when defining observation records or adding measurement to an authorized experience. Preserve the separation between actual behavior, interface events, and inferred benefit. Use a manual tally or existing records when those answer the question; adding an analytics service is optional.

## Start with the observation, not the tracking tool

For each proposed observation, name its definition, unit, denominator, eligible cohort, time window, data source, and known blind spots. Record the version of the offer and experience. Describe collection as planned until it has actually been implemented and inspected.

| Observation | What can establish it | What cannot substitute for it |
| --- | --- | --- |
| Exposure to the experience | An eligible person was actually shown the declared version | A deployment, a prepared message, or estimated impressions |
| Useful job completed | The person completed the specified decision or task under defined acceptance criteria | A result rendered, button clicked, or favorable AI review |
| Correct non-fit identified | Known constraints and an inspectable result support that the offer is unsuitable | Every rejected input or the sponsor losing a comparison |
| Qualified business outcome | The defined action occurred in reliable business records within its window | A CTA click, a draft booking, or an unverified lead |
| Recipient completed their own job | A distinct recipient used the experience and met its acceptance criteria | A copied link, original user's repeat visit, or social reach |
| Later re-sharing | A recipient initiated a subsequent sharing action within the defined window | Assuming every recipient shares, or treating an initiated share as delivered |

A useful experience can lead to no purchase. Record that result honestly. A purchase does not establish that the experience helped the person.

## Minimal records

Use only fields needed for the declared question. A manual aggregate record can contain:

- experience version and observation window;
- outcome name and precise definition;
- eligible denominator and observed count;
- source, collection method, and known missing data;
- actual marginal cost and operator time, where available.

Person-level linkage, account records, cookies, or new third-party tracking require an appropriate purpose and authorization. If independent people cannot be distinguished reliably, state that limitation; do not silently relabel visits as people. An arbitrary session identifier does not prove independence or identity.

Keep personal inputs, messages, access tokens, and sensitive answers out of public links, analytics payloads, and example fixtures. Publish only permitted aggregated results. Preserve source records according to the user's existing practices and applicable requirements; this guide does not establish a legal retention policy.

## Connect the three outcomes carefully

Retain separate records for customer usefulness, the qualified business outcome, and any recipient benefit. Do not join records by guessed identity or infer that a later purchase belongs to an earlier visitor without a defensible linkage method.

For experiments, preserve original assignment and consistent eligibility rules. Do not remove non-buyers from the denominator or compare selected tool completers with every control visitor. Inspect missing outcomes and unequal follow-up. If observation errors could differ between arms, repair or limit the conclusion.

Sharing and group coordination can create interference between people. Do not feed a network or cluster experiment to the independent-person calculator as if every recipient were independently assigned. Use an appropriate design and method, or report scoped descriptive evidence.

## Verify the observation path

Before exposure, exercise one ordinary completion, a genuine non-fit, an incomplete or invalid attempt, and any enabled recipient route. Verify the event or record actually appears in the intended permitted destination and keeps its correct definition. Do not call a mock handler or console print a working production analytics connection.

Keep test observations distinguishable from customer records. Confirm resets, retries, and repeat visits do not silently multiply the declared denominator. Verify that copying or downloading a result does not submit a booking, send an invitation, or count as a sale.

Record checks actually executed and their limits in `assets/learning-record.template.md`. A static code review cannot establish rendered browser behavior, delivered messages, customer utility, or instrumented production collection.
