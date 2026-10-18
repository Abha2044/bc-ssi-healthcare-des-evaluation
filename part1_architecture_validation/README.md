# Part 1 — Architecture validation (R7 pilot)

Does the baseline architecture satisfy requirement R7, and do the C4\*/C6\*
refinements change that answer?

R7 is the pilot. The same structure extends to the other requirements.

## Run it

Python 3.9+, no third-party packages. From this folder, in order:

```bash
python test_proposed_contracts.py        # 1. run the proposed R7 model (T1–T10)
python run_r7_variation_experiment.py    # 2. run it under 4 configurations x 2 profiles
python validate_architecture.py          # 3. structural checks on the models
python assess_variations.py              # 4. tabulate the documented variations
python assess_reference_coverage.py      # 5. compute coverage  <- main result
python compare_r7_controlled.py          # 6. controlled baseline vs refined
python build_r7_main_comparison.py       # 7. assemble the summary tables
```

Steps 5–7 read CSVs that steps 1–2 write, so the order matters.

## Expected result

Step 5 prints:

```
baseline                   : undetermined (8 supported, 0 unsupported, 3 unresolved)
C4_star_only               : undetermined (8 supported, 0 unsupported, 3 unresolved)
C6_star_only               : undetermined (8 supported, 0 unsupported, 3 unresolved)
C4_C6_star                 : undetermined (8 supported, 0 unsupported, 3 unresolved)
R7_proposed_logical_design : full         (11 supported, 0 unsupported, 0 unresolved)
```

**The refinement does not improve documentary coverage.** The three unresolved
checks are the C4→C6 obligation contract, the C6↔C15 scope contract, and the
final-release invariant. Naming C4.4 and C6.6 does not define those contracts,
so the verdict does not move. Only the proposed design, which specifies them,
reaches `full`.

Step 2 prints 8/8 accepted for every configuration under
`shared_responsibilities` — the control — and 2/8 vs 8/8 under
`atam_informed_availability`, where the baseline mechanisms are *assumed*
unavailable. That second profile shows what follows from the assumption; it
does not establish that the assumption is true.

## Where things are

| | |
|---|---|
| `models/` | the inputs — requirements, components, flows, assessments |
| `evidence/` | appendix extracts and the criterion derivation |
| `results/` | everything the scripts write (CSV + Markdown) |
| `docs/` | the written explanations |

## Which document to read

In this order. Each one is reached from here; none of them is a second entry point.

| Read | For | Length |
|---|---|---|
| 1. `docs/PART1_ONE_PAGE_SUMMARY.md` | the whole of Part 1 on one page | 31 lines |
| 2. `docs/R7_CHECKS_AND_EVIDENCE_GUIDE.md` | **how 1.1 and 1.2 are done**, check by check | 142 lines |
| 3. `evidence/r7_criterion_derivation.md` | why each criterion was defined, and its evidence threshold | |
| 4. `docs/COLLABORATOR_HANDOFF.md` | what Part 2 has to decide | 81 lines |

If you only read one thing, read **section C of the guide** — that is how the
requirement is traced to components and how each verdict is recorded.
