# R7 checks, code and evidence — detailed guide

**For review| Part 1.1 and Part 1.2**

Paths in code ticks are relative to `part1_architecture_validation/`. Start with the [one-page overview](PART1_ONE_PAGE_SUMMARY.md). The criterion-origin and evidence-threshold explanation is in [`evidence/r7_criterion_derivation.md`](../evidence/r7_criterion_derivation.md).

## Read this first: four different numbers

| Result | What is counted | Main file | Interpretation |
| --- | --- | --- | --- |       
| **8 supported + 3 unresolved + 2 N/A** | 13 **direct documentary assessment criteria** | `results/reference_requirement_coverage.csv` | Published baseline and ATAM-only configurations remain **undetermined** |
| **1 supported + 2 unresolved** | 3 **supplementary audit criteria** | `results/reference_supporting_flow_coverage.csv` and `reference_criterion_assessment.csv` | Kept separate from direct R7 criteria |
| **10/10 PASS** | 10 **selected executable test examples** | three `results/proposed_*_test_results.csv` files | Tests an explicitly **proposed logical realization**, not historical baseline software |  
| **8/8 vs 2/8** | 8 **variation cases** in two assumption profiles | `results/r7_controlled_comparison_summary.csv` | **Conditional** functional result, not measured reliability/uptime |

The 13+3 criteria are **analyst-derived and manually reviewed** from Appendix B's R7 flow and Appendix A's state/component descriptions. The Python aggregation does not discover the original verdicts or prove the assessed architecture was implemented.

## A. The exact 13 direct R7 criteria

**Source:** `models/r7_reference_assessment.json`, array `checks`; corresponding source interactions and evidence thresholds: `evidence/r7_criterion_derivation.md`. **Read the actual baseline verdict and rationale:** `results/reference_criterion_assessment.csv` (filter `configuration = baseline`).

| Criterion | What we assess | Baseline verdict | Primary source |
| --- | --- | --- | --- |
| `C4-DECISION` | C4 returns permit/deny from access/policy/consent context | **Supported** | Appendix B §A R7 / Table C R7 |
| `C4-OBLIGATIONS` | C4 returns restrictions/obligations with decision | **Supported** | Appendix B §A R7 / Table C R7 |
| `C6-DECISION` | C6 follows permit/deny as PEP | **Supported** | Appendix B §A R7 / Table C R7 |
| `C6-OBLIGATIONS` | C6 has masking/filtering enforcement responsibility | **Supported** | Appendix B §A R7 / Table C R7 |
| `C15-SCOPE` | C15 participates in scoped FHIR retrieval/filtering | **Supported** | Appendix B §A R7 / Table C R7 |
| `I1-REQUEST` | C6 gives C4 subject/resource/action/purpose/consent context | **Supported** | Appendix B §A R7 / Table C R7 |
| `I2-RESPONSE` | C4→C6 consistent obligation meaning, targets, failure handling | **Unresolved** | Appendix B mentions obligations but lacks this detailed assurance |
| `I3-SCOPE` | C6↔C15 share and maintain authorized records/fields/date scope | **Unresolved** | Both roles assigned, coordination not established |
| `I4-DATA` | C15→C6→client never releases unrestricted data | **Unresolved** | Filtering mentioned, final-release invariant not established |
| `STATE-POLICY` | C4.2 is the policy definition owner | **Supported** | Appendix A §A.0 / Table A-0 |
| `STATE-CONSENT` | C4.2 holds current consent for evaluation; C14 credentials | **Supported** | Appendix A §A.0, consent-role clarification |
| `STATE-REQUEST` | Persistent session/request state in this single-request pilot | **Not applicable** | Assessor's single-request scope decision |
| `STATE-CONSENT-COORDINATION` | Mid-request consent change propagation in fixed-snapshot pilot | **Not applicable** | Assessor's fixed-consent scope decision |

**Total:** 5 supported behaviours + 1 supported interface + 2 supported state checks = **8 supported**; I2/I3/I4 = **3 unresolved**; two state exclusions = **2 N/A**. Zero are marked unsupported. *Undetermined ≠ demonstrated failure.*

**Why these 13 are aggregated:** `models/r7_reference_assessment.json` contains two entries in `capabilities`, with `mandatory_checks` arrays. Their **union** gives the 13 direct checks. The audit checks are instead listed in `supplementary_flow_checks`.

## B. Three supplementary R7 audit checks (not included in 8/3/2)

| Check | Evidence / uncertainty | Verdict |
| --- | --- | --- |
| `C5-AUDIT` | C5 role for logging permit/deny is documented | Supported |
| `I5-AUDIT` | C6→C5 audit payload semantics and fields unclear | Unresolved |
| `C5-ENFORCEMENT-OUTCOME` | Whether applied/blocked restrictions are recorded remains unclear | Unresolved |

These appear in the **same** JSON `checks` array and `results/reference_criterion_assessment.csv`; they are explicitly identified by `supplementary_flow_checks` and summarized in `results/reference_supporting_flow_coverage.csv`. Keep this transparent: Appendix B includes auditing in R7, even though this pilot treats detailed audit assurance separately.

## C. How Part 1.1 is done

Part 1.1 answers: **which components cover R7, judged on behaviour, interfaces and
state ownership?** It runs as two pipelines. The first traces the requirement to
components. The second records and aggregates a verdict for each criterion.

### C.1 The requirement-to-component trace

```text
models/requirements.json          R7 -> 2 capabilities        names NO component
        |                         (Appendix B, Table C, capability-goal column only)
        |
models/flows.json                 C6 -> C4 -> C6+C15 -> C5    claims NO coverage
        |                         (Appendix B, Table C, runtime-flow column)
        |
models/components/C*.json         what each component does    names NO requirement
        |                         (Appendix A, Table A-0)
        |
models/capability_mappings.json   claim + citation            <- the ONLY join
        |
validate_architecture.py          structural checks
        |
results/component_contributions.csv, interface_validation.csv, capability_coverage.csv
```

**Why this is not circular.** The first three files are kept apart deliberately.
`requirements.json` mentions no component; `components/C*.json` mentions no
requirement; `flows.json` says who talks to whom but claims nothing about
capability. Nothing can "cover" anything until `capability_mappings.json` states
the claim in writing **with a source reference**, and the entries there are called
`candidate_providers`, not providers — a candidate is a claim to be assessed, not
a result.

The component files list only subcomponents Table A-0 actually names. A-0 names
C4.4, C5.5, C6.6, C12.5 and C17.5 as *absent*, so they do not appear. That
omission is data for the next stage, not an oversight.

### C.2 The criterion review

```text
Appendix B (R7 flow) + Appendix A (C4.2 / C14 / state)
        |  criterion derivation -> evidence/r7_criterion_derivation.md
models/r7_reference_assessment.json   16 checks, one recorded verdict each
        + models/refined_variations.json   configurations and overrides
        |  assess_reference_coverage.py : review(), classification(), run()
results/reference_criterion_assessment.csv    one row per configuration x check
results/reference_requirement_coverage.csv    8 / 3 / 2 per configuration
results/reference_supporting_flow_coverage.csv  audit, kept separate
results/r7_reference_architecture_report.md
```

Each of the 16 checks gets one of four verdicts — `supported`, `unsupported`,
`undetermined`, `not_applicable`. `review()` **rejects** any determined verdict
that lacks an assessor, a rationale and an evidence reference, so a citation on
its own never produces a verdict. `classification()` then applies fixed rules:
`full` if every applicable check is supported, `undetermined` if any mandatory
check is unresolved, and so on.

The script aggregates reviews. It does not discover them, and it cannot promote a
verdict because a test passed.

### C.3 Reading the result

Baseline and ATAM-only configurations: **8 supported, 3 unresolved, 2 N/A**.
The 8 are behaviour and state; all 3 unresolved are interfaces (I2, I3, I4).

The separate `R7_proposed_logical_design` reaches **11 supported, 0 unresolved,
2 N/A** within the same 13 direct checks, because it supplies explicit I2/I3/I4
rules. That does **not** change the published baseline's verdict.

**The finding:** 1.1 locates the deficiency at the interfaces between components,
not inside them. C4\* adds a named C4.4 and C6\* operationalises C6.6 — both
component-internal, neither defines a payload, a failure rule, or a split of
responsibility between two components. So all three interface checks stay
unresolved and the refinement does not move the verdict.

## D. Where the proposed I2–I4 tests are (supporting logical-model evidence)

| What is tested | Definition / code | Where results appear |
| --- | --- | --- |
| C4→C6 obligation response structure and masking/date obligations (**I2**) | `models/proposed_contracts.json` (`CONTRACT-R7-I2`); `test_proposed_contracts.py`: `validate_response()`, `enforce_reference()` | `results/proposed_contract_test_results.csv`: **R7-T1–T5** |
| Example policy/consent obligation selection (C4 responsibility; helps **I2**) | `models/refined_variations.json`: `proposed_selection_example`; `test_proposed_contracts.py`: `derive_policy_response()` | `results/proposed_selection_test_results.csv`: **R7-T6** |
| Authorized record scope and final restricted release (**I3/I4**) | `models/refined_variations.json`: `proposed_retrieval_example` and `proposed_logical_rules`; `test_proposed_contracts.py`: `retrieve_scoped_records()`, `enforce_with_retrieval()` | `results/proposed_retrieval_test_results.csv`: **R7-T7–T10** |

**Test meaning:** T1 denied access; T2 masking; T3 date filtering; T4 unsupported obligation safely blocked; T5 masking and date filtering together; T6 policy selection; T7 scoped retrieval and masking; T8 denial prevents retrieval; T9 missing scope blocks disclosure; T10 empty authorized scope releases no records.

The 10 examples passed in the recorded R7 pilot runs. They are selected proposed-model tests using synthetic flat records, **not** a deployed FHIR service or independent C4*/C6* implementations. The actual implementation supplies I3/I4 rules in `refined_variations.json` and Python; `proposed_contracts.json` primarily contains the formal I2 response contract and its test fixtures.

## E. Why C4* and C6* were selected (ATAM mapping)

| Finding | Appendix A reports | Variant model location | Do not infer |
| --- | --- | --- | --- |
| G2 → C4* | No dedicated C4.4 Obligation Handler in assessed baseline | `models/refined_variations.json` → `variations` → `C4_star` | Baseline C4 can never prepare obligations |
| G3 → C6* | C6.6 minimizer specified but reported not operationalized at gateway instances | `models/refined_variations.json` → `variations` → `C6_star` | A measured historical outage or measured failure rate |

`assess_variations.py` evaluates model variation definitions/ATAM trace information; it does **not** independently implement or verify either deployed subcomponent.

## F. Where the baseline-versus-refined experiment is (Part 1.2)

```text
models/proposed_contracts.json [same test data, expected outputs]
       + models/refined_variations.json [four configs, two profiles]
       ↓
test_proposed_contracts.py [shared logical helpers]
       ↓
run_r7_variation_experiment.py [four configs × two profiles × eight cases]
       ↓
results/r7_variation_experiment.csv [each case/condition]
results/r7_variation_experiment_summary.csv [numerical summary]
       ↓
compare_r7_controlled.py [checks equal cases/scope/oracles; produces paired report]
       ↓
results/r7_controlled_comparison.md
results/r7_controlled_comparison_summary.csv
results/r7_controlled_comparison_by_case.csv
```

| Profile | Baseline + same contracts | Both C4* + C6* + same contracts | What this supports |
| --- | --- | --- | --- |
| `shared_responsibilities` | **8/8** accepted | **8/8** accepted | No modeled advantage when baseline preparation/enforcement already available |
| `atam_informed_availability` | **2/8** accepted | **8/8** accepted | Combined refinements help **if** baseline preparation/enforcement are unavailable as assumed |

C4*-only = 3/8 and C6*-only = 2/8 in the restrictive profile (see original variation summary). Both profiles use the **same** I2/I3/I4 logical rules. The availability flags `baseline_preparation_available` and `baseline_enforcement_available` in `refined_variations.json` are **analyst assumptions**, not measurements.

**Do not present `compare_r7_controlled.py` as a second independent experiment**: it reuses `run_r7_variation_experiment.py` and the common test helpers.

## G. Other scripts and result files: what to show and what to keep

| Script | Function | Main outputs to consult | Paper priority |
| --- | --- | --- | --- |
| `validate_architecture.py` | Model/traceability and structural consistency checks | `capability_coverage.csv`, `component_contributions.csv`, `interface_validation.csv`, `requirement_coverage.csv` | Explain method briefly; detailed CSVs in GitHub |
| `assess_reference_coverage.py` | Aggregates manually justified criterion verdicts per architecture | `reference_criterion_assessment.csv`, `reference_requirement_coverage.csv`, `r7_reference_architecture_report.md` | **Primary Part 1.1** |
| `assess_variations.py` | Checks ATAM/refinement definitions and selected architectural variations | Variation assessment output (e.g., `atam_comparison.csv` when generated) | Short explanation / traceability |
| `test_proposed_contracts.py` | Tests selected proposed contract/selection/retrieval behaviour | Three `proposed_*_test_results.csv` files | One paragraph: 10/10 selected examples |
| `run_r7_variation_experiment.py` | Main deterministic scenario/assumption evaluation | `r7_variation_experiment.csv` + `_summary.csv` | Part 1.2 underlying experiment |
| `compare_r7_controlled.py` | Pairs/validates common test conditions and prepares comparison | `r7_controlled_comparison.md`, `_summary.csv`, `_by_case.csv` | **Primary Part 1.2 presentation** |
| `build_r7_main_comparison.py` | Consolidates **existing** results without changing verdicts | `r7_main_component_requirement_comparison.md` + `.csv` | Clear combined summary, not extra validation |

## H. How to trace **one** claim: I2 from requirement to code

1. **Requirement:** Appendix B R7 says C4 sends a decision and obligations to C6.
2. **Criterion:** `models/r7_reference_assessment.json` → `checks` → `I2-RESPONSE`: Do C4/C6 agree on the restriction meanings and failure treatment?
3. **Review verdict:** `results/reference_criterion_assessment.csv`: filter `configuration=baseline`, `check=I2-RESPONSE` → **undetermined**. Same for C4*/C6*-only variants.
4. **Proposed design:** `models/proposed_contracts.json` → `CONTRACT-R7-I2`, plus `models/refined_variations.json` → `proposed_logical_rules.I2-RESPONSE`.
5. **Functional evidence:** `test_proposed_contracts.py` executes enforcement and safe-failure cases; see T4/T5 (and T6 selection).
6. **Proposed-model verdict:** `reference_criterion_assessment.csv`, `configuration=R7_proposed_logical_design`, `check=I2-RESPONSE` → **supported** within the selected proposed scope.
7. **Limitation:** This cannot be transferred to the original baseline as proof of deployed component compatibility.

**Repository note:** The result files cited above are committed. They were previously untracked - not ignored, simply never added - so earlier clones of this repository did not contain them. Re-running the scripts regenerates them identically; `git status results/` should report no modifications after a clean run.

**One-sentence handoff:** *Part 1 documents 13 direct R7 checks (8 supported, 3 unresolved, 2 outside pilot), provides 10 selected proposed logical tests, and compares baseline/refined functional behaviour under two declared availability assumptions; the evidence is not a real implementation or an independent demonstration that the baseline fails R7.*
