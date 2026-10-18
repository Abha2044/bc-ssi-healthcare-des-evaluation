# R7 reference-architecture assessment

This report assesses the conceptual reference architecture using explicit criterion reviews. It does not infer a verdict from a citation or execute the component variants.

## Coverage rules

Full: all applicable mandatory checks are supported. Partial: supported and unsupported checks coexist with no unresolved checks. None: all applicable checks are unsupported. Any unresolved mandatory check, or no applicable checks, leaves coverage undetermined. Direct R7 coverage uses capability checks only. Supplementary audit is reported separately. Proposed-design results must not be interpreted as historical baseline evidence.

## Baseline-versus-refined component comparison

Descriptions come from refined_variations.json; interface criteria and uncertainty come from the recorded reviews. Appendix A operational findings retain their ATAM-derived origin. This table does not infer missing behaviour from a missing subcomponent name.

| Aspect | C4 baseline | C4* refined | C6 baseline | C6* refined |
| --- | --- | --- | --- | --- |
| Behaviour | C4 decides access and sends any restrictions. | Prepare restrictions to send with the C4 access decision. | C6 checks access and applies restrictions before releasing records. | Make data-minimization enforcement available at each C6 gateway. |
| Architectural difference | Appendix A lists C4.1-C4.3, but not a named C4.4 Obligation Handler. Reported origin: ATAM-derived, not independently verified | add_subcomponent / C4.4 / Obligation Handler. Preparing restrictions is not the same as applying them. | Appendix A reports C6.6 specified but not active at every gateway. Reported origin: ATAM-derived, not independently verified | operationalise_specified_capability / C6.6 / Data Minimizer. The baseline already describes masking and filtering as C6 duties. |
| Interfaces | Required interaction criteria (compatibility assessed separately): C6 sends request details to C4. / C4 and C6 agree on decision and restriction meanings. | C6 must understand the restrictions C4 sends; exact API is not specified. | Required interaction criteria (compatibility assessed separately): C6 sends request details to C4. / C4 and C6 agree on decision and restriction meanings. / C6 and C15 agree on which records can be returned. / Every restriction remains applied to the final response. / C6 sends C5 the information needed for audit. | C6 must understand restrictions and scope from C4/C15. |
| State | Policy definitions: C4.2 is the named policy registry. Actual storage and consistency are not tested. / Current consent state: C4.2 holds current consent. Consent synchronization is not tested. | No new persistent state owner is established. | Decision and obligations for the current request: No persistent owner is claimed. A temporary request does not require a stored session. | This request does not imply persistent session state. |
| Remaining uncertainty | I2-RESPONSE: Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? | I2-RESPONSE: Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? | I2-RESPONSE: Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? / I3-SCOPE: Which restrictions belong to C6 or C15? \| How is the authorized record scope preserved? / I4-DATA: Can any restricted data reappear before release? / I5-AUDIT: What audit event does C6 send to C5? | I2-RESPONSE: Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? / I3-SCOPE: Which restrictions belong to C6 or C15? \| How is the authorized record scope preserved? / I4-DATA: Can any restricted data reappear before release? / I5-AUDIT: What audit event does C6 send to C5? |
| Configuration coverage | baseline: undetermined (8 supported, 3 unresolved). Whole configuration, not component-alone coverage. | C4_star_only: undetermined (8 supported, 3 unresolved). Whole configuration, not component-alone coverage. | baseline: undetermined (8 supported, 3 unresolved). Whole configuration, not component-alone coverage. | C6_star_only: undetermined (8 supported, 3 unresolved). Whole configuration, not component-alone coverage. |
| Source basis | Requirements Appendix B, Section A R7 and Table C R7 / Appendix_A_corrected(1).docx, Table A-0 / Appendix_A_corrected(1).docx, Section A.0 consent-role clarification | Appendix_A_corrected(1).docx, Table A-11 / Appendix_A_corrected(1).docx, Table A-11.2 / Appendix_A_corrected(1).docx, Table A-13 | Requirements Appendix B, Section A R7 and Table C R7 / Appendix_A_corrected(1).docx, Table A-0 | Appendix_A_corrected(1).docx, Table A-11 / Appendix_A_corrected(1).docx, Table A-11.2 / Appendix_A_corrected(1).docx, Table A-12 |

C4* and C6* columns describe each individual replacement. The combined configuration is assessed in the results below. The separately labelled proposed logical design contains additional rules and must not be treated as evidence of a refinement-only improvement.

## Configuration results

| Configuration | Evidence type | Coverage | Supported | Unsupported | Unresolved | Not applicable |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | documented_baseline_design | undetermined | 8 | 0 | 3 | 2 |
| C4_star_only | atam_derived_refinement | undetermined | 8 | 0 | 3 | 2 |
| C6_star_only | atam_derived_refinement | undetermined | 8 | 0 | 3 | 2 |
| C4_C6_star | atam_derived_refinement | undetermined | 8 | 0 | 3 | 2 |
| R7_proposed_logical_design | proposed_design | full | 11 | 0 | 0 | 2 |

Reviews are inherited from the shared assessment unless an explicit configuration override is supplied. Identical results therefore do not establish that baseline and refined implementations behave identically.

## Capability coverage

| Configuration | Capability | Coverage | Unresolved checks |
| --- | --- | --- | --- |
| baseline | enforce_need_to_know_decision | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| baseline | enforce_disclosure_obligations | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| C4_star_only | enforce_need_to_know_decision | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| C4_star_only | enforce_disclosure_obligations | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| C6_star_only | enforce_need_to_know_decision | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| C6_star_only | enforce_disclosure_obligations | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| C4_C6_star | enforce_need_to_know_decision | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| C4_C6_star | enforce_disclosure_obligations | undetermined | I2-RESPONSE\|I3-SCOPE\|I4-DATA |
| R7_proposed_logical_design | enforce_need_to_know_decision | full | None |
| R7_proposed_logical_design | enforce_disclosure_obligations | full | None |

## Individual component contributions

Each result concerns that component’s assigned checks, not its ability to satisfy all of R7 alone.

| Configuration | Component | Contribution coverage | Unresolved checks |
| --- | --- | --- | --- |
| baseline | C14 | not_applicable | 0 |
| baseline | C15 | undetermined | 2 |
| baseline | C4 | undetermined | 1 |
| baseline | C5 | undetermined | 2 |
| baseline | C6 | undetermined | 4 |
| C4_star_only | C14 | not_applicable | 0 |
| C4_star_only | C15 | undetermined | 2 |
| C4_star_only | C4 | undetermined | 1 |
| C4_star_only | C5 | undetermined | 2 |
| C4_star_only | C6 | undetermined | 4 |
| C6_star_only | C14 | not_applicable | 0 |
| C6_star_only | C15 | undetermined | 2 |
| C6_star_only | C4 | undetermined | 1 |
| C6_star_only | C5 | undetermined | 2 |
| C6_star_only | C6 | undetermined | 4 |
| C4_C6_star | C14 | not_applicable | 0 |
| C4_C6_star | C15 | undetermined | 2 |
| C4_C6_star | C4 | undetermined | 1 |
| C4_C6_star | C5 | undetermined | 2 |
| C4_C6_star | C6 | undetermined | 4 |
| R7_proposed_logical_design | C14 | not_applicable | 0 |
| R7_proposed_logical_design | C15 | full | 0 |
| R7_proposed_logical_design | C4 | full | 0 |
| R7_proposed_logical_design | C5 | undetermined | 2 |
| R7_proposed_logical_design | C6 | undetermined | 1 |

## Supporting audit completeness

These checks do not determine direct R7 coverage.

| Configuration | Evidence type | Coverage | Unresolved checks |
| --- | --- | --- | --- |
| baseline | documented_baseline_design | undetermined | C5-ENFORCEMENT-OUTCOME\|I5-AUDIT |
| C4_star_only | atam_derived_refinement | undetermined | C5-ENFORCEMENT-OUTCOME\|I5-AUDIT |
| C6_star_only | atam_derived_refinement | undetermined | C5-ENFORCEMENT-OUTCOME\|I5-AUDIT |
| C4_C6_star | atam_derived_refinement | undetermined | C5-ENFORCEMENT-OUTCOME\|I5-AUDIT |
| R7_proposed_logical_design | proposed_design | undetermined | C5-ENFORCEMENT-OUTCOME\|I5-AUDIT |

## Separate ATAM comparison

This supplied interpretation is not independently reproduced gap evidence.

| ATAM gap | Interpretation |
| --- | --- |
| G2 | C4* adds a named handler, but baseline already documents obligations. |
| G3 | C6* makes enforcement explicit, but baseline already documents filtering. |
|  | I2, I3 and I4 are still unclear in baseline evidence; this is not a newly proven gap. |

## R7 executable variation comparison

Source: r7_variation_experiment_summary.csv. The figures below are read from the saved CSV; this report generator does not execute the experiment. Regenerate experimental results after changing model or runner inputs.

| Profile | Configuration | Accepted cases | Complete permitted delivery | Correct C4 selection | Privacy protected |
| --- | --- | --- | --- | --- | --- |
| shared_responsibilities | baseline | 8/8 | 5/5 | 3/3 | 8/8 |
| shared_responsibilities | C4_star_only | 8/8 | 5/5 | 3/3 | 8/8 |
| shared_responsibilities | C6_star_only | 8/8 | 5/5 | 3/3 | 8/8 |
| shared_responsibilities | C4_C6_star | 8/8 | 5/5 | 3/3 | 8/8 |
| atam_informed_availability | baseline | 2/8 | 0/5 | 0/3 | 8/8 |
| atam_informed_availability | C4_star_only | 3/8 | 0/5 | 3/3 | 8/8 |
| atam_informed_availability | C6_star_only | 2/8 | 0/5 | 0/3 | 8/8 |
| atam_informed_availability | C4_C6_star | 8/8 | 5/5 | 3/3 | 8/8 |

C4 selection is assessed only in the policy/consent-derived cases; supplied-decision cases do not assess selection. Accepted cases satisfy the selected response expectations and, where applicable, selection expectations. Privacy protection alone does not imply correct permitted delivery: blocked authorized requests remain incomplete delivery.

### shared_responsibilities

Assume all four configurations can prepare and enforce restrictions.

All four modeled configurations meet the selected case expectations under this profile. These cases demonstrate no functional advantage for the combined refinement under these assumptions.

### atam_informed_availability

Assume baseline preparation and enforcement are unavailable, based on ATAM concerns. This is not proven.

The combined configuration meets every selected case expectation; at least one other configuration does not. The difference is conditional on this profile’s availability assumptions.

All configurations reuse the same functional helpers when mechanisms are available. The shared-responsibility profile is therefore a consistency/robustness check, not evidence from four independently implemented architectures.

The availability profile explores ATAM-informed assumptions. Absence of a named subcomponent does not independently prove a baseline capability is unavailable. The comparison measures consequences of those assumptions; it does not discover historical baseline gaps, independently confirm ATAM, or update documentary verdicts.

This is a bounded functional experiment, not DES or a performance measurement. Trusted scope and fixed policy/consent are inputs; audit delivery, patient binding and consent updates are outside the executable cases.

## Reviewed criteria and evidence

### baseline

| Check | Kind | Verdict | Review origin | Rationale | Review evidence | Open questions |
| --- | --- | --- | --- | --- | --- | --- |
| C4-DECISION | behaviour | supported | shared_assessment | Appendix B assigns policy and consent decisions to C4. This documents the role, not the running code. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C4-OBLIGATIONS | behaviour | supported | shared_assessment | Appendix B says C4 returns obligations with its decision. It does not prove every rule is selected correctly. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C6-DECISION | behaviour | supported | shared_assessment | Appendix B describes permitted access and denial through C6. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C6-OBLIGATIONS | behaviour | supported | shared_assessment | Appendix B assigns masking and filtering to C6. Full execution is assessed separately. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C15-SCOPE | behaviour | supported | shared_assessment | Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-AUDIT | behaviour | supported | shared_assessment | Appendix B assigns access logging to C5; detailed enforcement logs are not proven. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| I1-REQUEST | interface | supported | shared_assessment | Appendix B specifies subject, resource, action, purpose and relevant consent in the policy flow. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| I2-RESPONSE | interface | undetermined | shared_assessment | The flow mentions obligations but does not define their shared meaning or failure handling. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? |
| I3-SCOPE | interface | undetermined | shared_assessment | The flow assigns both roles but does not explain their shared scope rules. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Which restrictions belong to C6 or C15? \| How is the authorized record scope preserved? |
| I4-DATA | interface | undetermined | shared_assessment | The flow requires filtering but does not show how later release steps preserve it. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Can any restricted data reappear before release? |
| I5-AUDIT | interface | undetermined | shared_assessment | The audit interaction is named, but the required event contents are unclear. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | What audit event does C6 send to C5? |
| STATE-POLICY | state | supported | shared_assessment | Appendix A lists C4.2 as the Policy Registry; actual storage is not verified. | Appendix_A_corrected(1).docx, Table A-0 |  |
| STATE-CONSENT | state | supported | shared_assessment | Appendix A Section A.0 assigns current consent to C4.2, separately from C14 credentials. | Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |
| STATE-REQUEST | state | not_applicable | shared_assessment | Not needed in this one-request pilot. This does not prove the whole gateway is stateless. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-ENFORCEMENT-OUTCOME | behaviour | undetermined | shared_assessment | The documents do not clearly establish this extra audit detail. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Does C5 record applied and blocked restrictions? |
| STATE-CONSENT-COORDINATION | state | not_applicable | shared_assessment | Not assessed: the selected request uses fixed consent; updates are outside scope. | r7_reference_assessment.json, assessment_scope: analyst-selected fixed-snapshot boundary \| Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |

### C4_star_only

| Check | Kind | Verdict | Review origin | Rationale | Review evidence | Open questions |
| --- | --- | --- | --- | --- | --- | --- |
| C4-DECISION | behaviour | supported | shared_assessment | Appendix B assigns policy and consent decisions to C4. This documents the role, not the running code. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C4-OBLIGATIONS | behaviour | supported | configuration_override | C4* adds the named C4.4 handler. That clarifies who prepares restrictions, not whether C6 understands them. | Appendix_A_corrected(1).docx, Table A-11.2 \| Appendix_A_corrected(1).docx, Table A-13 |  |
| C6-DECISION | behaviour | supported | shared_assessment | Appendix B describes permitted access and denial through C6. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C6-OBLIGATIONS | behaviour | supported | shared_assessment | Appendix B assigns masking and filtering to C6. Full execution is assessed separately. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C15-SCOPE | behaviour | supported | shared_assessment | Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-AUDIT | behaviour | supported | shared_assessment | Appendix B assigns access logging to C5; detailed enforcement logs are not proven. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| I1-REQUEST | interface | supported | shared_assessment | Appendix B specifies subject, resource, action, purpose and relevant consent in the policy flow. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| I2-RESPONSE | interface | undetermined | shared_assessment | The flow mentions obligations but does not define their shared meaning or failure handling. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? |
| I3-SCOPE | interface | undetermined | shared_assessment | The flow assigns both roles but does not explain their shared scope rules. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Which restrictions belong to C6 or C15? \| How is the authorized record scope preserved? |
| I4-DATA | interface | undetermined | shared_assessment | The flow requires filtering but does not show how later release steps preserve it. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Can any restricted data reappear before release? |
| I5-AUDIT | interface | undetermined | shared_assessment | The audit interaction is named, but the required event contents are unclear. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | What audit event does C6 send to C5? |
| STATE-POLICY | state | supported | shared_assessment | Appendix A lists C4.2 as the Policy Registry; actual storage is not verified. | Appendix_A_corrected(1).docx, Table A-0 |  |
| STATE-CONSENT | state | supported | shared_assessment | Appendix A Section A.0 assigns current consent to C4.2, separately from C14 credentials. | Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |
| STATE-REQUEST | state | not_applicable | shared_assessment | Not needed in this one-request pilot. This does not prove the whole gateway is stateless. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-ENFORCEMENT-OUTCOME | behaviour | undetermined | shared_assessment | The documents do not clearly establish this extra audit detail. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Does C5 record applied and blocked restrictions? |
| STATE-CONSENT-COORDINATION | state | not_applicable | shared_assessment | Not assessed: the selected request uses fixed consent; updates are outside scope. | r7_reference_assessment.json, assessment_scope: analyst-selected fixed-snapshot boundary \| Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |

### C6_star_only

| Check | Kind | Verdict | Review origin | Rationale | Review evidence | Open questions |
| --- | --- | --- | --- | --- | --- | --- |
| C4-DECISION | behaviour | supported | shared_assessment | Appendix B assigns policy and consent decisions to C4. This documents the role, not the running code. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C4-OBLIGATIONS | behaviour | supported | shared_assessment | Appendix B says C4 returns obligations with its decision. It does not prove every rule is selected correctly. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C6-DECISION | behaviour | supported | shared_assessment | Appendix B describes permitted access and denial through C6. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C6-OBLIGATIONS | behaviour | supported | configuration_override | C6* makes C6.6 operationally explicit; the baseline already documents filtering. | Appendix_A_corrected(1).docx, Table A-11.2 \| Appendix_A_corrected(1).docx, Table A-13 |  |
| C15-SCOPE | behaviour | supported | shared_assessment | Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-AUDIT | behaviour | supported | shared_assessment | Appendix B assigns access logging to C5; detailed enforcement logs are not proven. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| I1-REQUEST | interface | supported | shared_assessment | Appendix B specifies subject, resource, action, purpose and relevant consent in the policy flow. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| I2-RESPONSE | interface | undetermined | shared_assessment | The flow mentions obligations but does not define their shared meaning or failure handling. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? |
| I3-SCOPE | interface | undetermined | shared_assessment | The flow assigns both roles but does not explain their shared scope rules. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Which restrictions belong to C6 or C15? \| How is the authorized record scope preserved? |
| I4-DATA | interface | undetermined | shared_assessment | The flow requires filtering but does not show how later release steps preserve it. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Can any restricted data reappear before release? |
| I5-AUDIT | interface | undetermined | shared_assessment | The audit interaction is named, but the required event contents are unclear. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | What audit event does C6 send to C5? |
| STATE-POLICY | state | supported | shared_assessment | Appendix A lists C4.2 as the Policy Registry; actual storage is not verified. | Appendix_A_corrected(1).docx, Table A-0 |  |
| STATE-CONSENT | state | supported | shared_assessment | Appendix A Section A.0 assigns current consent to C4.2, separately from C14 credentials. | Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |
| STATE-REQUEST | state | not_applicable | shared_assessment | Not needed in this one-request pilot. This does not prove the whole gateway is stateless. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-ENFORCEMENT-OUTCOME | behaviour | undetermined | shared_assessment | The documents do not clearly establish this extra audit detail. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Does C5 record applied and blocked restrictions? |
| STATE-CONSENT-COORDINATION | state | not_applicable | shared_assessment | Not assessed: the selected request uses fixed consent; updates are outside scope. | r7_reference_assessment.json, assessment_scope: analyst-selected fixed-snapshot boundary \| Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |

### C4_C6_star

| Check | Kind | Verdict | Review origin | Rationale | Review evidence | Open questions |
| --- | --- | --- | --- | --- | --- | --- |
| C4-DECISION | behaviour | supported | shared_assessment | Appendix B assigns policy and consent decisions to C4. This documents the role, not the running code. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C4-OBLIGATIONS | behaviour | supported | configuration_override | C4* adds the named C4.4 handler. Shared meaning with C6 is still open. | Appendix_A_corrected(1).docx, Table A-11.2 \| Appendix_A_corrected(1).docx, Table A-13 |  |
| C6-DECISION | behaviour | supported | shared_assessment | Appendix B describes permitted access and denial through C6. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C6-OBLIGATIONS | behaviour | supported | configuration_override | C6* makes C6.6 operationally explicit; contract meaning is still unproven. | Appendix_A_corrected(1).docx, Table A-11.2 \| Appendix_A_corrected(1).docx, Table A-13 |  |
| C15-SCOPE | behaviour | supported | shared_assessment | Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-AUDIT | behaviour | supported | shared_assessment | Appendix B assigns access logging to C5; detailed enforcement logs are not proven. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| I1-REQUEST | interface | supported | shared_assessment | Appendix B specifies subject, resource, action, purpose and relevant consent in the policy flow. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| I2-RESPONSE | interface | undetermined | shared_assessment | The flow mentions obligations but does not define their shared meaning or failure handling. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Do C4 and C6 agree on restrictions? \| What happens if a restriction cannot be applied? |
| I3-SCOPE | interface | undetermined | shared_assessment | The flow assigns both roles but does not explain their shared scope rules. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Which restrictions belong to C6 or C15? \| How is the authorized record scope preserved? |
| I4-DATA | interface | undetermined | shared_assessment | The flow requires filtering but does not show how later release steps preserve it. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Can any restricted data reappear before release? |
| I5-AUDIT | interface | undetermined | shared_assessment | The audit interaction is named, but the required event contents are unclear. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | What audit event does C6 send to C5? |
| STATE-POLICY | state | supported | shared_assessment | Appendix A lists C4.2 as the Policy Registry; actual storage is not verified. | Appendix_A_corrected(1).docx, Table A-0 |  |
| STATE-CONSENT | state | supported | shared_assessment | Appendix A Section A.0 assigns current consent to C4.2, separately from C14 credentials. | Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |
| STATE-REQUEST | state | not_applicable | shared_assessment | Not needed in this one-request pilot. This does not prove the whole gateway is stateless. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-ENFORCEMENT-OUTCOME | behaviour | undetermined | shared_assessment | The documents do not clearly establish this extra audit detail. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Does C5 record applied and blocked restrictions? |
| STATE-CONSENT-COORDINATION | state | not_applicable | shared_assessment | Not assessed: the selected request uses fixed consent; updates are outside scope. | r7_reference_assessment.json, assessment_scope: analyst-selected fixed-snapshot boundary \| Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |

### R7_proposed_logical_design

| Check | Kind | Verdict | Review origin | Rationale | Review evidence | Open questions |
| --- | --- | --- | --- | --- | --- | --- |
| C4-DECISION | behaviour | supported | shared_assessment | Appendix B assigns policy and consent decisions to C4. This documents the role, not the running code. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C4-OBLIGATIONS | behaviour | supported | configuration_override | A fixed proposed policy and consent example produces the expected restrictions (T6). This is not a complete policy engine. | Requirements Appendix B, Section A R7 and Table C R7 \| refined_variations.json, proposed_selection_example \| test_proposed_contracts.py, derive_policy_response \| results/proposed_selection_test_results.csv, R7-T6 |  |
| C6-DECISION | behaviour | supported | shared_assessment | Appendix B describes permitted access and denial through C6. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| C6-OBLIGATIONS | behaviour | supported | configuration_override | C6* makes the enforcement role explicit; the proposed tests assess selected actions separately. | Appendix_A_corrected(1).docx, Table A-11.2 \| Appendix_A_corrected(1).docx, Table A-13 |  |
| C15-SCOPE | behaviour | supported | shared_assessment | Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-AUDIT | behaviour | supported | shared_assessment | Appendix B assigns access logging to C5; detailed enforcement logs are not proven. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| I1-REQUEST | interface | supported | shared_assessment | Appendix B specifies subject, resource, action, purpose and relevant consent in the policy flow. | Requirements Appendix B, Section A R7 \| Requirements Appendix B, Table C R7 |  |
| I2-RESPONSE | interface | supported | configuration_override | The proposed contract defines masking, date filtering and safe blocking. Selected examples support these rules only. | proposed_contracts.json, CONTRACT-R7-I2 \| refined_variations.json, proposed_logical_rules.I2-RESPONSE \| test_proposed_contracts.py, validate_response and enforce_reference \| results/proposed_contract_test_results.csv, R7-T4 and R7-T5 \| results/proposed_selection_test_results.csv, R7-T6 |  |
| I3-SCOPE | interface | supported | configuration_override | The proposed model uses trusted allowed record IDs; C15 filters IDs/dates and C6 masks. Scope origin is assumed. | test_proposed_contracts.py, retrieve_scoped_records \| test_proposed_contracts.py, enforce_with_retrieval \| test_proposed_contracts.py, run_retrieval_examples \| results/proposed_retrieval_test_results.csv, R7-T7 to R7-T10 |  |
| I4-DATA | interface | supported | configuration_override | The proposed model releases only the restricted result; failed restrictions release no records. Not a real FHIR service. | test_proposed_contracts.py, retrieve_scoped_records \| test_proposed_contracts.py, enforce_with_retrieval \| test_proposed_contracts.py, enforce_reference \| results/proposed_contract_test_results.csv, R7-T5 \| results/proposed_retrieval_test_results.csv, R7-T7 to R7-T10 |  |
| I5-AUDIT | interface | undetermined | shared_assessment | The audit interaction is named, but the required event contents are unclear. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | What audit event does C6 send to C5? |
| STATE-POLICY | state | supported | shared_assessment | Appendix A lists C4.2 as the Policy Registry; actual storage is not verified. | Appendix_A_corrected(1).docx, Table A-0 |  |
| STATE-CONSENT | state | supported | shared_assessment | Appendix A Section A.0 assigns current consent to C4.2, separately from C14 credentials. | Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |
| STATE-REQUEST | state | not_applicable | shared_assessment | Not needed in this one-request pilot. This does not prove the whole gateway is stateless. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 |  |
| C5-ENFORCEMENT-OUTCOME | behaviour | undetermined | shared_assessment | The documents do not clearly establish this extra audit detail. | RequirementsAppendixB-refined(1).docx, Section A R7 \| RequirementsAppendixB-refined(1).docx, Table C R7 | Does C5 record applied and blocked restrictions? |
| STATE-CONSENT-COORDINATION | state | not_applicable | shared_assessment | Not assessed: the selected request uses fixed consent; updates are outside scope. | r7_reference_assessment.json, assessment_scope: analyst-selected fixed-snapshot boundary \| Appendix_A_corrected(1).docx, Section A.0 consent-role clarification |  |

## Interpretation

Resolve open criteria through cited source review or an explicitly identified proposed design. A proposed contract can support a proposed variation; it does not establish historical baseline compatibility. Unknown state ownership should be assessed only where the selected behaviour requires retained state. ATAM alignment and operational experiment results remain separate from this coverage calculation.

Implementation assurance: not assessed. Source truth and assessor judgments are not automatically verified.
