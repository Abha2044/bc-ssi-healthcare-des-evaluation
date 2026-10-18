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
