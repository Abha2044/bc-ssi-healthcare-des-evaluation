# R7: Baseline versus ATAM-refined architecture — traceable comparison

> Generated from existing JSON models and CSV results. No new experiment was performed. 
> This report distinguishes **documentary coverage**, **ATAM interpretation**, and **assumption-based model execution**.

## Question: Does the refinement cover R7 better?

The documentary assessment **does not currently establish higher R7 coverage** for C4*, C6*, or their combination. The executable experiment **does demonstrate improved completion of selected permitted cases** for the combined configuration **when baseline preparation and enforcement are assumed unavailable**.

## 1. Documentary requirement coverage

| Architecture | Supported | Unsupported | Unresolved | N/A | Coverage |
| --- | --- | --- | --- | --- | --- |
| baseline | 8 | 0 | 3 | 2 | undetermined |
| C4_star_only | 8 | 0 | 3 | 2 | undetermined |
| C6_star_only | 8 | 0 | 3 | 2 | undetermined |
| C4_C6_star | 8 | 0 | 3 | 2 | undetermined |
| R7_proposed_logical_design | 11 | 0 | 0 | 2 | full |

The separately specified **proposed logical design** has extra I2/I3/I4 rules; its `full` label applies only to the selected model criteria and must **not** be transferred to the refinement-only configurations.

## 2. Requirement → component → ATAM → refinement → validated consequence

### 1. C4-OBLIGATIONS — C4
- **Required:** C4 returns the decision and required restrictions.
- **Baseline documentary assessment:** supported — Appendix B says C4 returns obligations with its decision. It does not prove every rule is selected correctly.
- **ATAM finding:** G2. G2: separately named C4.4 absent in assessed inventory; 
- **Refined responsibility:** C4* / C4.4 Obligation Handler.
- **Refinement-only documentary check:** C4* = supported; C6* = supported; combined = supported.
- **Available executable evidence:** R7-V6, R7-V7, R7-V8. Preparation availability is enabled in the C4* configurations; these reuse one selection helper.
- **Limit:** Not a separate implementation or proof the published C4 could not prepare obligations.
- **Source:** RequirementsAppendixB-refined(1).docx, Section A R7 | RequirementsAppendixB-refined(1).docx, Table C R7

### 2. C6-OBLIGATIONS — C6
- **Required:** C6 applies masking and filtering before release.
- **Baseline documentary assessment:** supported — Appendix B assigns masking and filtering to C6. Full execution is assessed separately.
- **ATAM finding:** G3. G3: C6.6 availability questioned by ATAM; 
- **Refined responsibility:** C6* / C6.6 Data Minimizer.
- **Refinement-only documentary check:** C4* = supported; C6* = supported; combined = supported.
- **Available executable evidence:** R7-T2, R7-T3, R7-T5, R7-V6, R7-V8. C4* alone blocks permitted delivery when enforcement is assumed unavailable; combined design delivers 5/5 permitted cases.
- **Limit:** Not an independently executed C6* service; baseline already documents filtering duties.
- **Source:** RequirementsAppendixB-refined(1).docx, Section A R7 | RequirementsAppendixB-refined(1).docx, Table C R7

### 3. I2-RESPONSE — C4 + C6
- **Required:** C4 and C6 agree on decision and restriction meanings.
- **Baseline documentary assessment:** undetermined — The flow mentions obligations but does not define their shared meaning or failure handling.
- **ATAM finding:** G2 + G3. G2: separately named C4.4 absent in assessed inventory; G3: C6.6 availability questioned by ATAM; 
- **Refined responsibility:** C4* + C6* interaction.
- **Refinement-only documentary check:** C4* = undetermined; C6* = undetermined; combined = undetermined.
- **Available executable evidence:** R7-T4, R7-T5, R7-T6, R7-V6. The proposed shared decision/obligation representation is exercised by the model.
- **Limit:** Compatibility of published baseline or refinement-only interfaces is not independently established.
- **Source:** RequirementsAppendixB-refined(1).docx, Section A R7 | RequirementsAppendixB-refined(1).docx, Table C R7

### 4. C15-SCOPE — C15
- **Required:** C15 serves only the records allowed by the requested scope.
- **Baseline documentary assessment:** supported — Appendix B assigns scoped FHIR retrieval and filters to C15. Coordination with C6 still needs review.
- **ATAM finding:** None. No direct ATAM change identified for this interface.
- **Refined responsibility:** C15 (unchanged).
- **Refinement-only documentary check:** C4* = supported; C6* = supported; combined = supported.
- **Available executable evidence:** R7-T7, R7-T8, R7-T9, R7-T10. A separate proposed logical model restricts flat records by supplied allowed IDs and dates.
- **Limit:** Scope origin and actual FHIR service behaviour are not tested.
- **Source:** RequirementsAppendixB-refined(1).docx, Section A R7 | RequirementsAppendixB-refined(1).docx, Table C R7

### 5. I3-SCOPE — C6 + C15
- **Required:** C6 and C15 agree on which records can be returned.
- **Baseline documentary assessment:** undetermined — The flow assigns both roles but does not explain their shared scope rules.
- **ATAM finding:** None specific to I3. No direct ATAM change identified for this interface.
- **Refined responsibility:** C6* + C15 interaction.
- **Refinement-only documentary check:** C4* = undetermined; C6* = undetermined; combined = undetermined.
- **Available executable evidence:** R7-T7, R7-T9, R7-T10, R7-V6, R7-V7, R7-V8. Proposed scope rules are tested against synthetic records.
- **Limit:** The authority and derivation of allowed IDs and variant-level contract compatibility remain unverified.
- **Source:** RequirementsAppendixB-refined(1).docx, Section A R7 | RequirementsAppendixB-refined(1).docx, Table C R7

### 6. I4-DATA — C6 + C15
- **Required:** Every restriction remains applied to the final response.
- **Baseline documentary assessment:** undetermined — The flow requires filtering but does not show how later release steps preserve it.
- **ATAM finding:** G3 (related). G3: C6.6 availability questioned by ATAM; 
- **Refined responsibility:** C6* + C15 release path.
- **Refinement-only documentary check:** C4* = undetermined; C6* = undetermined; combined = undetermined.
- **Available executable evidence:** R7-T2, R7-T3, R7-T5, R7-T7, R7-T9, R7-V6. Proposed logical model masks/filters before release and fails closed for invalid restrictions/scope.
- **Limit:** An actual deployed release pipeline and its end-to-end enforcement are not evaluated.
- **Source:** RequirementsAppendixB-refined(1).docx, Section A R7 | RequirementsAppendixB-refined(1).docx, Table C R7

## 3. All direct R7 check verdicts

| Check | Component(s) | Baseline | C4* | C6* | Combined | Proposed design |
| --- | --- | --- | --- | --- | --- | --- |
| C4-DECISION | C4 | supported | supported | supported | supported | supported |
| C4-OBLIGATIONS | C4 | supported | supported | supported | supported | supported |
| C6-DECISION | C6 | supported | supported | supported | supported | supported |
| C6-OBLIGATIONS | C6 | supported | supported | supported | supported | supported |
| C15-SCOPE | C15 | supported | supported | supported | supported | supported |
| I1-REQUEST | C4\|C6 | supported | supported | supported | supported | supported |
| I2-RESPONSE | C4\|C6 | undetermined | undetermined | undetermined | undetermined | supported |
| I3-SCOPE | C6\|C15 | undetermined | undetermined | undetermined | undetermined | supported |
| I4-DATA | C6\|C15 | undetermined | undetermined | undetermined | undetermined | supported |
| STATE-POLICY | C4 | supported | supported | supported | supported | supported |
| STATE-CONSENT | C4 | supported | supported | supported | supported | supported |
| STATE-REQUEST | C6 | not_applicable | not_applicable | not_applicable | not_applicable | not_applicable |
| STATE-CONSENT-COORDINATION | C4\|C14 | not_applicable | not_applicable | not_applicable | not_applicable | not_applicable |

**I2, I3 and I4 remain undetermined in all four documentary configurations.** State checks are included when applicable; `STATE-REQUEST` and `STATE-CONSENT-COORDINATION` are not applicable to this fixed-snapshot pilot.

## 4. Controlled variation experiment

### Shared responsibilities available

| Configuration | Accepted | Permitted delivery | Selection correct | Privacy protected |
| --- | --- | --- | --- | --- |
| baseline | 8/8 | 5/5 | 3/3 | 8/8 |
| C4_star_only | 8/8 | 5/5 | 3/3 | 8/8 |
| C6_star_only | 8/8 | 5/5 | 3/3 | 8/8 |
| C4_C6_star | 8/8 | 5/5 | 3/3 | 8/8 |

### ATAM-informed limited baseline availability

| Configuration | Accepted | Permitted delivery | Selection correct | Privacy protected |
| --- | --- | --- | --- | --- |
| baseline | 2/8 | 0/5 | 0/3 | 8/8 |
| C4_star_only | 3/8 | 0/5 | 3/3 | 8/8 |
| C6_star_only | 2/8 | 0/5 | 0/3 | 8/8 |
| C4_C6_star | 8/8 | 5/5 | 3/3 | 8/8 |

**Interpretation note:** A zero in `Selection correct` under the limited-availability profile does **not** prove that C4 selected obligations incorrectly. In that configuration, execution stopped when preparation was assumed unavailable, so selection was not observed.

**Acceptance note:** A deliberately blocked disclosure can pass a negative expectation (for example, R7-T4) without demonstrating successful authorized delivery.

### Exactly what changed in each ATAM-informed test

| Case | Expectation | Baseline | C4* | C6* | Combined |
| --- | --- | --- | --- | --- | --- |
| R7-T1 | Deny prevents disclosure | PASS (denied) | PASS (denied) | PASS (denied) | PASS (denied) |
| R7-T2 | Mask removes prohibited field | FAIL (preparation_blocked) | FAIL (enforcement_blocked) | FAIL (preparation_blocked) | PASS (permitted) |
| R7-T3 | Date filtering excludes older record | FAIL (preparation_blocked) | FAIL (enforcement_blocked) | FAIL (preparation_blocked) | PASS (permitted) |
| R7-T4 | Unsupported obligation blocks disclosure | PASS (preparation_blocked) | PASS (enforcement_blocked) | PASS (preparation_blocked) | PASS (enforcement_blocked) |
| R7-T5 | Mask and date filter apply together | FAIL (preparation_blocked) | FAIL (enforcement_blocked) | FAIL (preparation_blocked) | PASS (permitted) |
| R7-V6 | Apply both restrictions to allowed records | FAIL (preparation_blocked) | FAIL (enforcement_blocked) | FAIL (preparation_blocked) | PASS (permitted) |
| R7-V7 | Block access if scope is missing | FAIL (preparation_blocked) | PASS (enforcement_blocked) | FAIL (preparation_blocked) | PASS (enforcement_blocked) |
| R7-V8 | Return no records when scope is empty | FAIL (preparation_blocked) | FAIL (enforcement_blocked) | FAIL (preparation_blocked) | PASS (permitted) |

Only the **availability flags** differ across configurations in the current runner. All use `derive_policy_response` and `enforce_with_retrieval` from `test_proposed_contracts.py`. The current code does **not** execute independently specified C4/C4* or C6/C6* implementations. A blocked request can preserve privacy without delivering data.

## 5. What can and cannot be concluded

- **Demonstrated by documentary mapping:** R7 responsibilities are documented. I2, I3, I4 and full component-level compatibility remain unresolved for baseline and refinement-only configurations.
- **Demonstrated by executable model:** Under ATAM-informed unavailability assumptions, C4* + C6* meets all eight selected expectations while the baseline meets two.
- **Demonstrated by proposed logical model:** The chosen model rules for the selected obligation exchange, record scope, and final release cases pass their bounded tests.
- **Not proven:** The published baseline lacks obligation preparation/enforcement; the variant components have mutually compatible implementation interfaces; the complete real-world R7 requirement is satisfied.

## 6. Minimum additional evidence needed for a stronger refinement-coverage claim

1. **I2:** Specify and independently review what C4* sends and C6* accepts (decision, action, fields, date bounds, invalid/unsupported obligations, fail-closed handling).
2. **I3:** State who derives the authorized scope and how the C6* → C15 interaction preserves it; test provider/consumer agreement against the same fixed expected outputs.
3. **I4:** Specify the single final-release invariant: all mandatory restrictions must be applied or no records are released; independently check the whole proposed path.
4. Record those items as **proposed refinement contract evidence**, with independent review and linked tests. Reassess the refinement configurations only when those assertions are justified. Do not copy `proposed_design` verdicts into historical baseline verdicts.

Supporting C5 audit adequacy (I5 and enforcement-outcome logging) is assessed separately. No real FHIR server, independent variant implementations, scope derivation, consent update, deployment, or performance evidence is included.

### Reproduce

Run existing validators/experiment first, then `python part1_architecture_validation/build_r7_comparison.py`. Outputs are this file, `r7_component_traceability_comparison.csv`, and `r7_all_criterion_verdicts.csv`.
