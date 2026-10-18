# R7 — Requirement-to-component baseline/refinement comparison

> Generated from existing Part 1 results. No new tests were performed and no coverage verdicts were changed.
> ATAM findings motivate assumptions; the executable variants share model helpers and are not independent component implementations.

## Main research result: Does the refinement improve R7 coverage?

| Validation question | Baseline evidence | ATAM gap / refined change | Combined refinement evidence | Executable evidence | Still needed |
| --- | --- | --- | --- | --- | --- |
| Can C4 prepare the required obligations? | supported: Appendix B says C4 returns obligations with its decision. It does not prove every rule is selected correctly. | G2 (ATAM); C4* adds named C4.4 Obligation Handler (Appendix A, A-11). | supported: C4* adds the named C4.4 handler. Shared meaning with C6 is still open. | Policy selection outcomes in limited profile: baseline 0/0; combined 3/3. Baseline selection was blocked by the assumed unavailability, not shown incorrect. | Demonstrate correct obligation selection and C4* provider behaviour independently. |
| Can C6 enforce the required restrictions? | undetermined: Table A-0 states that the C6.6 Data Minimizer is specified as a Privacy & Policy responsibility but not enforced at any gateway instance, and lists no other C6 subcomponent performing masking or filtering. The responsibility is assigned; the mechanism is not established. | G3 (ATAM); C6* operationalizes already-specified C6.6 minimization (Appendix A, A-11). | supported: C6* names C6.6 Data Minimizer as available at each gateway instance. | Complete permitted deliveries in limited profile: baseline 0/5; combined 5/5. This measures the whole modeled path, not isolated C6*. | Show C6* implements mandatory masking/filtering for selected requests. |
| Do C4 and C6 agree on obligation meaning? | undetermined: The flow mentions obligations but does not define their shared meaning or failure handling. | G2/G3 related; C4.4 prepares obligations; C6.6 enforces them; common semantics are still needed. | undetermined: The flow mentions obligations but does not define their shared meaning or failure handling. | Proposed I2 decision/obligation rules are exercised, not a separately executed baseline/variant interface. | Specify and review shared payload, semantics, and failure handling for C4* to C6*. |
| Does C15 provide authorized scoped records? | supported: Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | No direct C15 variation in this R7 pilot; C15 is unchanged in the C4*/C6* variation comparison. | supported: Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | Proposed flat-record retrieval is tested using a supplied authorized scope. | Confirm actual C15 retrieval enforcement and source of authorized scope. |
| Do C6 and C15 preserve the same scope? | undetermined: The flow assigns both roles but does not explain their shared scope rules. | G3 related; no direct I3 closure; The refinement must define the C6*/C15 responsibility split and scope contract. | undetermined: The flow assigns both roles but does not explain their shared scope rules. | Proposed scoped retrieval tests run, but there are no independently executed variant interfaces. | Specify authorized scope provenance and provider/consumer compatibility. |
| Are restrictions preserved to final release? | undetermined: The flow requires filtering but does not show how later release steps preserve it. | G3 related; C6.6 availability alone does not prove end-to-end release invariants. | undetermined: The flow requires filtering but does not show how later release steps preserve it. | The proposed logical model enforces restrictions or blocks release in selected cases. | Review/test the complete refined release path, including failures and combined restrictions. |
| Does the complete architecture satisfy R7? | undetermined (8 supported, 4 unresolved, 2 N/A) | Combined C4.4 preparation and C6.6 enforcement availability (G2/G3). | undetermined (9 supported, 3 unresolved, 2 N/A) | Limited-assumption acceptance: baseline 3/8; combined 8/8. With shared availability: both 8/8. | Resolve I2/I3/I4 with evidence attributable to the defined combined refinement; do not transfer proposed-model verdicts. |

**Interpretation:** C4*+C6* yields better authorized delivery under the ATAM-informed limited-availability assumptions, but the available documentary criteria do not establish a higher R7 coverage verdict for the refinement-only configurations.

## Architectural coverage by configuration (1.1 and 1.2)

| Configuration | Supported | Unresolved | N/A | Overall R7 coverage |
| --- | --- | --- | --- | --- |
| baseline | 8 | 4 | 2 | undetermined |
| C4_star_only | 8 | 4 | 2 | undetermined |
| C6_star_only | 9 | 3 | 2 | undetermined |
| C4_C6_star | 9 | 3 | 2 | undetermined |
| R7_proposed_logical_design | 12 | 0 | 2 | full |

The proposed logical design includes additional contract assumptions. Its `full` verdict is bounded to its selected criteria; it is not a measured coverage improvement of the C4*/C6* refinements alone.

## Executable comparison by assumption profile (1.2)

### shared_responsibilities

| Configuration | Accepted | Complete permitted delivery | Correct C4 selection | Privacy protected |
| --- | --- | --- | --- | --- |
| baseline | 8/8 | 5/5 | 3/3 | 8/8 |
| C4_star_only | 8/8 | 5/5 | 3/3 | 8/8 |
| C6_star_only | 8/8 | 5/5 | 3/3 | 8/8 |
| C4_C6_star | 8/8 | 5/5 | 3/3 | 8/8 |

### atam_informed_availability

| Configuration | Accepted | Complete permitted delivery | Correct C4 selection | Privacy protected |
| --- | --- | --- | --- | --- |
| baseline | 3/8 | 0/5 | 0/0 | 8/8 |
| C4_star_only | 3/8 | 0/5 | 3/3 | 8/8 |
| C6_star_only | 3/8 | 0/5 | 0/0 | 8/8 |
| C4_C6_star | 8/8 | 5/5 | 3/3 | 8/8 |

**Caution:** When preparation is unavailable, selection is blocked rather than independently evaluated. Privacy protection includes blocking a request and does not imply successful delivery.

## Traceable proposed-model tests (not baseline evidence)

| Question | Criterion | Baseline verdict | Combined verdict | Proposed verdict | Existing proposed tests |
| --- | --- | --- | --- | --- | --- |
| Can C4 prepare the required obligations? | C4-OBLIGATIONS | supported | supported | supported | R7-T6: PASS |
| Can C6 enforce the required restrictions? | C6-OBLIGATIONS-MECHANISM | undetermined | supported | supported | R7-T2: PASS; R7-T3: PASS; R7-T5: PASS |
| Do C4 and C6 agree on obligation meaning? | I2-RESPONSE | undetermined | undetermined | supported | R7-T4: PASS; R7-T5: PASS; R7-T6: PASS |
| Does C15 provide authorized scoped records? | C15-SCOPE | supported | supported | supported | R7-T7: PASS; R7-T8: PASS; R7-T9: PASS; R7-T10: PASS |
| Do C6 and C15 preserve the same scope? | I3-SCOPE | undetermined | undetermined | supported | R7-T7: PASS; R7-T9: PASS; R7-T10: PASS |
| Are restrictions preserved to final release? | I4-DATA | undetermined | undetermined | supported | R7-T5: PASS; R7-T7: PASS; R7-T9: PASS |

## What this demonstrates

- **1.1:** Documents the assigned R7 behaviours and identifies unresolved I2 (obligations), I3 (scope), and I4 (final release) interface evidence.
- **1.2:** The modeled combined refinement improves expected authorized delivery under the ATAM-informed availability assumptions; no improvement appears when all mechanisms are assumed available.
- **Not proven:** Historical baseline inability, independent C4*/C6* implementation compatibility, or full real-world R7 satisfaction. Supporting audit checks are assessed separately.

## How to support a stronger refined-coverage claim

1. Specify and independently review a C4* -> C6* decision-and-obligation interface (I2).
2. Specify/review the C6* -> C15 authorization-scope contract (I3).
3. Specify/review the final-release invariant (I4), and execute targeted tests against the declared *refined* interfaces rather than only a shared proposed helper.
4. Reassess documentary coverage using attributable evidence; do not auto-promote verdicts from test counts.

Sources: Appendix A, Tables A-0/A-3/A-11/A-13; Requirements Appendix B, R7 flow and Table C; `reference_criterion_assessment.csv`, `reference_requirement_coverage.csv`, `r7_variation_experiment_summary.csv`, and proposed test result CSVs.
