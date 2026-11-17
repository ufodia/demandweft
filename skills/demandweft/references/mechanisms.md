# Usable proof mechanisms

Resolve one evidenced customer decision barrier with one usable intervention. Choose the smallest mechanism that can change the decision. Treat an inferred barrier as a hypothesis until customer evidence supports it.

## Contents

- Select a mechanism
- Keep outcomes separate
- Six mechanism contracts
- Build and verify the deliverable
- Fictional worked examples

## Select a mechanism

| Customer's unresolved question | Candidate mechanism | Required grounding |
| --- | --- | --- |
| Is this suitable for my situation? | Fit explorer | Actual eligibility, exclusions, and unknowns |
| Will it work on something like mine? | Same-logic sample | Working implementation or a verified delivery method |
| Is this preferable to my alternatives? | Decision comparator | Current, comparable evidence for the alternatives |
| Can I change without losing something? | Switch rehearsal | A reversible test environment and explicit invariants |
| How do I get the other decision makers aligned? | Coordination artifact | Their real criteria and a concrete shared decision |
| Can someone else adapt this useful result? | Portable result | A safe reusable input/output boundary |

Do not add all six mechanisms. If the barrier concerns product failure, unavailable capacity, or an unsuitable offer, repair or narrow the offer before producing persuasion material. If evidence is absent, make the next evidence-gathering step explicit; do not invent customer objections.

## Keep outcomes separate

| Outcome | Observe | Do not substitute |
| --- | --- | --- |
| Customer value | A relevant task completed, a material uncertainty resolved, or correct self-disqualification | Page views, aesthetic quality, or an agent's approval |
| Business value | The preregistered qualified action and its delivery economics | General usefulness, downloads, or stated enthusiasm |
| Propagation, if justified | Another recipient obtains value and optionally creates a useful next result | Share-button clicks, raw impressions, or compulsory invitations |

Public benefit alone does not establish demand, willingness to pay, or economical acquisition. A customer choosing another option can be a successful customer outcome and an unsuccessful business hypothesis. Record both.

Define denominators, observation windows, costs, and invalid-test conditions before exposure. Derive thresholds from the actual decision and economics; do not invent universal priority scores or conversion targets. Omit propagation when there is no natural recipient benefit.

## Six mechanism contracts

### 1. Fit explorer

- **Input:** Obtain the offer's real eligibility rules, exclusions, capacity constraints, and the minimum information needed to distinguish them.
- **Actual output:** Build a working short questionnaire or fillable decision aid that returns suitable, unsuitable, or needs clarification, with reasons and a useful next step.
- **Customer benefit:** Help the person determine suitability before investing in a call, visit, account, or purchase.
- **Business hypothesis:** Better self-selection may improve qualified inquiries or reduce avoidable service work; measure this separately.
- **Optional next-recipient value:** Offer a blank or safely reset version that helps another person assess their own situation.
- **Wrong-fit path:** Explain the exclusion without pressuring the person to buy; give a supported alternative or a neutral next step.
- **Validation:** Exercise every result branch and unknown input. Verify that missing information never becomes an unsupported positive recommendation.

### 2. Same-logic sample

- **Input:** Obtain a bounded customer-like input, the real processing function or delivery method, and its expected limitations. Use synthetic examples by default.
- **Actual output:** Produce an inspectable sample result through that implementation, with editable inputs or an explicitly bounded demonstration and a usable output file when relevant.
- **Customer benefit:** Let the person judge applicability and quality on a concrete task before committing.
- **Business hypothesis:** Experiencing the relevant capability may increase qualified activation or purchase at an acceptable delivery cost.
- **Optional next-recipient value:** Share a sanitized example or empty input template another person can run for their own task.
- **Wrong-fit path:** Reject unsupported inputs or reveal an inadequate result. Do not silently replace failures with invented success.
- **Validation:** Check supported and unsupported cases. For a separate interface, compare identical inputs against the source implementation. Label mocks, simulations, and unverified parity explicitly.

### 3. Decision comparator

- **Input:** Obtain the buyer's decision criteria and current primary evidence for the offer, competitors, manual work, and doing nothing where relevant.
- **Actual output:** Build an editable comparison or scenario calculator with visible assumptions, source dates, unknowns, and an explanation of what changes the recommendation.
- **Customer benefit:** Make tradeoffs inspectable for the person's own constraints.
- **Business hypothesis:** A substantiated advantage may improve qualified selection within the segment where that advantage applies.
- **Optional next-recipient value:** Let a colleague review the same assumptions or change them for another scenario.
- **Wrong-fit path:** Allow an alternative or no purchase to win. Do not use hidden weights or invented competitor weaknesses to force the preferred result.
- **Validation:** Verify comparable units, periods, and inclusions. Check sensitivity to uncertain inputs; separate estimates from quoted prices and observed results.

### 4. Switch rehearsal

- **Input:** Obtain the current workflow, intended replacement, representative safe fixtures, and what must survive the transition.
- **Actual output:** Run a reversible migration or workflow rehearsal in isolation and deliver the resulting sample, differences, failures, and restoration instructions.
- **Customer benefit:** Reveal actual switching effort and possible losses before a commitment.
- **Business hypothesis:** Reducing a verified switching obstacle may increase qualified trials while keeping onboarding costs viable.
- **Optional next-recipient value:** Provide a sanitized checklist or fixture pack a decision partner can inspect or use independently.
- **Wrong-fit path:** Identify blockers or unacceptable loss; recommend a narrower pilot, remaining with the current solution, or another option.
- **Validation:** Check the agreed invariants and restoration using the rehearsal artifacts. Distinguish a documented plan from an executed rehearsal; never use live customer systems as an unannounced test.

### 5. Coordination artifact

- **Input:** Obtain the real stakeholders, their criteria, unresolved dependencies, and the single decision they need to make.
- **Actual output:** Produce an editable decision brief, requirements checklist, annotated comparison, or meeting aid that another stakeholder can use without the original conversation.
- **Customer benefit:** Reduce the work required to explain, verify, and coordinate a decision.
- **Business hypothesis:** Clearer shared understanding may reduce stalled qualified opportunities or shorten the measured decision process.
- **Optional next-recipient value:** Make the recipient's task explicit: check a requirement, supply a missing fact, or compare an alternative.
- **Wrong-fit path:** Surface disagreement, missing evidence, or a valid reason to defer. Do not manufacture approval or consensus.
- **Validation:** Check that claims have sources, open questions remain visible, and the artifact exposes no unnecessary private information. Prepare sharing material without sending it automatically.

### 6. Portable result

- **Input:** Select a real product result, the inputs safe to retain, fields the recipient may change, and the implementation that will recompute it.
- **Actual output:** Add a usable result view with a clear adaptation action; recompute for the recipient and let them voluntarily create a new result. Keep the original unchanged.
- **Customer benefit:** Transfer a useful starting point while allowing a new person to solve their own task.
- **Business hypothesis:** Useful guest experiences may produce qualified adoption at a bounded compute and support cost.
- **Optional next-recipient value:** Specify the concrete benefit of the adapted result. Preserve a non-sharing route through the experience.
- **Wrong-fit path:** Return a supported limitation or allow the recipient to start afresh; do not promise that one person's result fits another.
- **Validation:** Reuse the production logic or verify behavioral parity. Test private-field removal, input limits, ownership isolation, expired/revoked shares, and guest cost limits. Keep private algorithms and credentials server-side; state any network dependency honestly.

## Build and verify the deliverable

Deliver the usable instrument, its actual output on safe fixtures, and the experiment contract. A concept, screenshot, or specification alone is not a built instrument. Use the smallest appropriate format: a working page, spreadsheet, sample file, or editable decision aid.

Record which behavior was executed and which remains unverified. Check relevant invalid inputs and the wrong-fit path. Keep sensitive data out of public URLs, examples, screenshots, and analytics. Do not publish, contact people, or incur unapproved external spending merely because the instrument is ready.

## Fictional worked examples

These examples illustrate implementation choices only. They are not completed research, customer evidence, or observed commercial results.

### Local service: neighborhood bicycle workshop

Assume a fictional workshop's verified service list covers ordinary brakes and chains but excludes electric drive units. The hypothesized barrier is uncertainty about whether a visit will be worthwhile.

Build a short working fit explorer using bicycle type, affected component, and a plain-language symptom. Collect no name, address, photo, or other identifying detail. Return an appropriate workshop service, a specialist referral category, or a request for clarification. Avoid diagnosing safety-critical mechanical faults from the questionnaire.

Open the artifact and exercise the ordinary-chain, electric-drive, and insufficient-information branches. Show the actual outputs. Offer an optional booking path only after a suitable result; do not send a booking request automatically.

Measure correct routing as customer value. Separately test whether qualified attended appointments justify the tool's cost. Sharing a blank explorer is optional and has no assumed viral effect.

### SaaS: CSV cleanup before import

Assume a fictional SaaS already has a CSV normalization function and the hypothesized barrier is whether it will handle the prospect's format without corrupting data.

Build a usable preview around that actual function with synthetic fixtures: a supported CSV, a quoted field containing a comma, and an unsupported layout. Produce the real downloadable cleaned file, an inspectable change summary, and an explicit unsupported-format result.

Run the function and the preview on identical fixtures, compare outputs, and record the result. If source implementation access is unavailable, report parity as unverified; do not describe a reimplementation as the production engine.

Test successful cleanup separately from qualified paid activation. If a recipient can benefit, add a resettable template link with isolated inputs and bounded guest execution. Validate costs and privacy before enabling public access; a working local artifact is still a complete reviewable deliverable.
