# Controlled R7 comparison: baseline + contracts vs. refined + contracts

## Research design

**Purpose:** Compare the functional consequences of C4*/C6* with the **same proposed** I2 (obligations), I3 (scope), and I4 (final release) logical contracts in both architectures.

**Control:** The script uses the original `run_r7_variation_experiment.py` and `test_proposed_contracts.py` helpers for all configurations. It verifies identical case IDs, expected policy responses, expected releases, and trusted scopes; no separate baseline/refined behavioural algorithms or test oracles are used.

**Change:** Only the binary assumed availability of C4 obligation preparation and C6 enforcement varies. The starred components stand for making these capabilities available; the model does not execute separate historical implementations.

| Controlled factor | Baseline + contracts | Refined C4* + C6* + contracts |
| --- | --- | --- |
| I2, I3, I4 logic | Same proposed rules | Same proposed rules |
| Inputs / expected outputs | Same 8 cases | Same 8 cases |
| `shared_responsibilities` | C4/C6 available (assumed) | C4*/C6* available (assumed) |
| `atam_informed_availability` | C4/C6 unavailable (assumed) | C4*/C6* available (assumed) |

**Evidence basis:** Appendix B describes baseline R7 responsibilities; Appendix A reports ATAM-derived G2/G3 concerns. Neither document proves an actual baseline inability to prepare or enforce obligations. The second profile is a sensitivity assumption, not a measured fact.

## Paired results

| Availability profile | Baseline accepted | Refined accepted | Difference | Baseline complete permitted deliveries | Refined complete permitted deliveries | Privacy protected |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `shared_responsibilities` | 8/8 | 8/8 | +0 cases | 5/5 | 5/5 | Baseline 8/8; refined 8/8 |
| `atam_informed_availability` | 2/8 | 8/8 | +6 cases | 0/5 | 5/5 | Baseline 8/8; refined 8/8 |

**Interpretation:** The first profile is a control: if baseline mechanisms work, the model does not reveal a functional advantage from the starred names. The second profile asks what follows *if* the ATAM-reported mechanisms are unavailable in the baseline. It does not establish that they truly are unavailable.

**Important:** Privacy protection counts cases that safely block data. Such blocked requests do **not** count as successful authorized delivery.

## Single-refinement checks (same experiment, not additional tests)

| Profile | Baseline | C4* only | C6* only | Both |
| --- | ---: | ---: | ---: | ---: |
| `shared_responsibilities` | 8/8 | 8/8 | 8/8 | 8/8 |
| `atam_informed_availability` | 2/8 | 3/8 | 2/8 | 8/8 |

## Criterion-level and interface evidence

| Interface | Shared proposed rule | Evidence limit |
| --- | --- | --- |
| I2: C4 → C6 | Common decision/obligation meanings; reject unsupported restrictions | Uses one shared helper; not independently implemented C4/C4* services |
| I3: C6 ↔ C15 | Filter trusted allowed record IDs and dates before release | Scope provenance is assumed and C15 is synthetic, not a FHIR deployment |
| I4: final data | Release only completely filtered/masked results, otherwise block | No real gateway or end-to-end implementation evaluated |

The experiment evaluates bounded functional behaviour, **not** documentary requirement coverage. It does not independently settle baseline/refined interface compatibility. Separate `R7_proposed_logical_design` coverage applies only to the explicitly specified and tested proposed model.

## Existing documentary R7 coverage (not recalculated from experiment)

| Configuration | Coverage | Supported | Unresolved | Not applicable |
| --- | --- | ---: | ---: | ---: |
| `baseline` | undetermined | 8 | 3 | 2 |
| `C4_C6_star` | undetermined | 8 | 3 | 2 |
| `R7_proposed_logical_design` | full | 11 | 0 | 2 |

## What this design does *not* prove

- No independent proof that the published baseline lacks C4/C6 capability; the baseline already assigns these logical responsibilities.
- No measured component reliability, uptime, fault probability, latency, or DES results; the availability inputs are Boolean assumptions and the test is deterministic.
- No improvement in **documented direct R7 coverage** can be inferred from higher test acceptance.
- No claim that a named C4.4/C6.6 is the unique way to satisfy R7; the required capabilities might be allocated to baseline components with equivalent behaviour.
- The experiments use one shared proposed implementation, synthetic records, trusted scope, and fixed consent rather than two deployed architectures.

## Reproducibility

Run from repository root: `python part1_architecture_validation/compare_r7_controlled.py`

Input fingerprints (first 12 hexadecimal characters of SHA-256):

- `models/proposed_contracts.json`: `e56a082c8440`
- `models/refined_variations.json`: `8531f8cbd2ff`
- `run_r7_variation_experiment.py`: `85f9bf859be1`
- `test_proposed_contracts.py`: `73898bcf68c2`

Identical case/scope/oracle checks passed for 8 cases across all four configurations and both model profiles.
