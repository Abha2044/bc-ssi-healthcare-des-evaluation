"""Controlled R7 comparison: same I2-I4 contracts, baseline vs C4*+C6*.

Requires the existing run_r7_variation_experiment.py and test_proposed_contracts.py.
Reuses their implementation and cases; adds NO new test logic or coverage verdicts.
Runs both model profiles and writes three comparison artifacts to results/.

From repository root:
    python part1_architecture_validation/compare_r7_controlled.py
"""

import argparse
import csv
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from run_r7_variation_experiment import run

BASELINE = 'baseline'
REFINED = 'C4_C6_star'
PROFILE_ORDER = ('shared_responsibilities', 'atam_informed_availability')
CONFIG_ORDER = (BASELINE, 'C4_star_only', 'C6_star_only', REFINED)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def output_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def expected_signature(row):
    # C4 response, permitted output and trusted scope are held constant.
    return tuple(json.dumps(json.loads(row[field]), sort_keys=True)
                 for field in ('expected_c4_response', 'expected_result', 'scope'))


def text_bool(value):
    return 'available' if value else 'unavailable'


def compare(contracts, variations, coverage, output_dir):
    # This invokes the existing model rather than replaying stale CSV files.
    with tempfile.TemporaryDirectory(prefix='r7_controlled_') as temp:
        rows, summaries = run(contracts, variations, Path(temp))

    doc = json.loads(variations.read_text(encoding='utf-8-sig'))
    profiles = {p['id']: p for p in doc['executable_comparison']['profiles']}
    if any(p not in profiles for p in PROFILE_ORDER):
        raise ValueError('Expected both shared_responsibilities and atam_informed_availability profiles.')
    if (profiles[PROFILE_ORDER[0]]['baseline_preparation_available'] is not True or
            profiles[PROFILE_ORDER[0]]['baseline_enforcement_available'] is not True or
            profiles[PROFILE_ORDER[1]]['baseline_preparation_available'] is not False or
            profiles[PROFILE_ORDER[1]]['baseline_enforcement_available'] is not False):
        raise ValueError('The documented two-profile assumptions differ from the input JSON.')
    index = {(r['profile'], r['configuration'], r['test']): r for r in rows}
    tests_by_group = defaultdict(set)
    oracles_by_test = defaultdict(set)
    for r in rows:
        tests_by_group[(r['profile'], r['configuration'])].add(r['test'])
        oracles_by_test[r['test']].add(expected_signature(r))
    test_ids = sorted(tests_by_group[(PROFILE_ORDER[0], BASELINE)])
    if not test_ids:
        raise ValueError('No common R7 cases found.')
    if any(tests_by_group.get((p, c)) != set(test_ids)
           for p in PROFILE_ORDER for c in CONFIG_ORDER):
        raise ValueError('The configurations are NOT using the same cases.')
    if any(len(oracles_by_test[test]) != 1 for test in test_ids):
        raise ValueError('Different expected C4 responses, outputs or scopes were detected!')
    # With all relevant mechanisms available, configuration labels must not
    # silently change the executed algorithm or its output.
    for test in test_ids:
        b = index[(PROFILE_ORDER[0], BASELINE, test)]
        for configuration in CONFIG_ORDER[1:]:
            variant = index[(PROFILE_ORDER[0], configuration, test)]
            if (variant['actual_result'] != b['actual_result'] or
                    variant['case_acceptance'] != b['case_acceptance']):
                raise ValueError('Uncontrolled difference in shared profile: ' + test)

    sindex = {(s['profile'], s['configuration']): s for s in summaries}
    if any(key not in sindex for key in ((p, c) for p in PROFILE_ORDER for c in CONFIG_ORDER)):
        raise ValueError('A profile/configuration summary is missing.')

    coverage_index = {}
    if coverage.exists():
        for cr in load_csv(coverage):
            if cr.get('requirement') == 'R7':
                coverage_index[cr['configuration']] = cr

    pair_rows = []
    for p in PROFILE_ORDER:
        for test in test_ids:
            b = index[(p, BASELINE, test)]
            r = index[(p, REFINED, test)]
            pair_rows.append({
                'profile': p, 'case': test, 'description': b['name'],
                'common_oracle_and_scope': 'verified_equal',
                'baseline_preparation_available': b['c4_preparation_available'],
                'baseline_enforcement_available': b['c6_enforcement_available'],
                'refined_preparation_available': r['c4_preparation_available'],
                'refined_enforcement_available': r['c6_enforcement_available'],
                'baseline_outcome': b['actual_outcome'],
                'refined_outcome': r['actual_outcome'],
                'baseline_acceptance': b['case_acceptance'],
                'refined_acceptance': r['case_acceptance'],
                'baseline_complete_delivery': b['permitted_data_delivery'],
                'refined_complete_delivery': r['permitted_data_delivery'],
                'baseline_privacy_protected': b['privacy_protected_for_case'],
                'refined_privacy_protected': r['privacy_protected_for_case'],
            })

    comparison_rows = []
    for p in PROFILE_ORDER:
        b = sindex[(p, BASELINE)]
        r = sindex[(p, REFINED)]
        comparison_rows.append({
            'profile': p,
            'profile_origin': profiles[p]['evidence_type'],
            'baseline_prep_assumed': text_bool(profiles[p]['baseline_preparation_available']),
            'baseline_enforce_assumed': text_bool(profiles[p]['baseline_enforcement_available']),
            'refined_prep_assumed': 'available',
            'refined_enforce_assumed': 'available',
            'same_contracts_cases_scopes_oracles': 'yes_verified',
            'cases': b['cases'],
            'baseline_accepted': b['accepted_cases'],
            'refined_accepted': r['accepted_cases'],
            'accepted_difference': r['accepted_cases'] - b['accepted_cases'],
            'permitted_cases': b['permit_cases'],
            'baseline_complete_delivery': b['complete_permitted_delivery_cases'],
            'refined_complete_delivery': r['complete_permitted_delivery_cases'],
            'baseline_privacy_protected': b['privacy_protected_cases'],
            'refined_privacy_protected': r['privacy_protected_cases'],
            'baseline_documentary_R7_coverage': coverage_index.get(BASELINE, {}).get('coverage', 'not_loaded'),
            'refined_documentary_R7_coverage': coverage_index.get(REFINED, {}).get('coverage', 'not_loaded'),
            'reliability_or_runtime_availability_measured': 'no',
        })

    lines = [
        '# Controlled R7 comparison: baseline + contracts vs. refined + contracts',
        '',
        '## Research design',
        '',
        '**Purpose:** Compare the functional consequences of C4*/C6* with the **same proposed** '
        'I2 (obligations), I3 (scope), and I4 (final release) logical contracts in both architectures.',
        '',
        '**Control:** The script uses the original `run_r7_variation_experiment.py` and '
        '`test_proposed_contracts.py` helpers for all configurations. It verifies identical case IDs, '
        'expected policy responses, expected releases, and trusted scopes; no separate baseline/refined '
        'behavioural algorithms or test oracles are used.',
        '',
        '**Change:** Only the binary assumed availability of C4 obligation preparation and C6 '
        'enforcement varies. The starred components stand for making these capabilities available; '
        'the model does not execute separate historical implementations.',
        '',
        '| Controlled factor | Baseline + contracts | Refined C4* + C6* + contracts |',
        '| --- | --- | --- |',
        '| I2, I3, I4 logic | Same proposed rules | Same proposed rules |',
        '| Inputs / expected outputs | Same 8 cases | Same 8 cases |',
        '| `shared_responsibilities` | C4/C6 available (assumed) | C4*/C6* available (assumed) |',
        '| `atam_informed_availability` | C4/C6 unavailable (assumed) | C4*/C6* available (assumed) |',
        '',
        '**Evidence basis:** Appendix B describes baseline R7 responsibilities; Appendix A reports '
        'ATAM-derived G2/G3 concerns. Neither document proves an actual baseline inability to prepare '
        'or enforce obligations. The second profile is a sensitivity assumption, not a measured fact.',
        '',
        '## Paired results',
        '',
        '| Availability profile | Baseline accepted | Refined accepted | Difference | '
        'Baseline complete permitted deliveries | Refined complete permitted deliveries | Privacy protected |',
        '| --- | ---: | ---: | ---: | ---: | ---: | --- |',
    ]
    for p in PROFILE_ORDER:
        b, r = (sindex[(p, c)] for c in (BASELINE, REFINED))
        lines.append(f"| `{p}` | {b['accepted_cases']}/{b['cases']} | "
                     f"{r['accepted_cases']}/{r['cases']} | "
                     f"+{r['accepted_cases'] - b['accepted_cases']} cases | "
                     f"{b['complete_permitted_delivery_cases']}/{b['permit_cases']} | "
                     f"{r['complete_permitted_delivery_cases']}/{r['permit_cases']} | "
                     f"Baseline {b['privacy_protected_cases']}/{b['cases']}; "
                     f"refined {r['privacy_protected_cases']}/{r['cases']} |")
    lines += [
        '',
        '**Interpretation:** The first profile is a control: if baseline mechanisms work, the '
        'model does not reveal a functional advantage from the starred names. The second profile '
        'asks what follows *if* the ATAM-reported mechanisms are unavailable in the baseline. '
        'It does not establish that they truly are unavailable.',
        '',
        '**Important:** Privacy protection counts cases that safely block data. Such blocked '
        'requests do **not** count as successful authorized delivery.',
        '',
        '## Single-refinement checks (same experiment, not additional tests)',
        '',
        '| Profile | Baseline | C4* only | C6* only | Both |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    for p in PROFILE_ORDER:
        numbers = [f"{sindex[(p, c)]['accepted_cases']}/{sindex[(p, c)]['cases']}" for c in CONFIG_ORDER]
        lines.append('| `' + p + '` | ' + ' | '.join(numbers) + ' |')
    lines += [
        '',
        '## Criterion-level and interface evidence',
        '',
        '| Interface | Shared proposed rule | Evidence limit |',
        '| --- | --- | --- |',
        '| I2: C4 → C6 | Common decision/obligation meanings; reject unsupported restrictions | '
        'Uses one shared helper; not independently implemented C4/C4* services |',
        '| I3: C6 ↔ C15 | Filter trusted allowed record IDs and dates before release | '
        'Scope provenance is assumed and C15 is synthetic, not a FHIR deployment |',
        '| I4: final data | Release only completely filtered/masked results, otherwise block | '
        'No real gateway or end-to-end implementation evaluated |',
        '',
        'The experiment evaluates bounded functional behaviour, **not** documentary '
        'requirement coverage. It does not independently settle baseline/refined interface '
        'compatibility. Separate `R7_proposed_logical_design` coverage applies only to the '
        'explicitly specified and tested proposed model.',
        '',
        '## Existing documentary R7 coverage (not recalculated from experiment)',
        '',
        '| Configuration | Coverage | Supported | Unresolved | Not applicable |',
        '| --- | --- | ---: | ---: | ---: |',
    ]
    for c in (BASELINE, REFINED, 'R7_proposed_logical_design'):
        cr = coverage_index.get(c)
        if cr:
            lines.append(f"| `{c}` | {cr['coverage']} | {cr['supported_checks']} | "
                         f"{cr['unresolved_checks']} | {cr['not_applicable_checks']} |")
        else:
            lines.append(f'| `{c}` | Not loaded from coverage CSV | — | — | — |')
    lines += [
        '',
        '## What this design does *not* prove',
        '',
        '- No independent proof that the published baseline lacks C4/C6 capability; '
        'the baseline already assigns these logical responsibilities.',
        '- No measured component reliability, uptime, fault probability, latency, or DES results; '
        'the availability inputs are Boolean assumptions and the test is deterministic.',
        '- No improvement in **documented direct R7 coverage** can be inferred from higher test acceptance.',
        '- No claim that a named C4.4/C6.6 is the unique way to satisfy R7; the required '
        'capabilities might be allocated to baseline components with equivalent behaviour.',
        '- The experiments use one shared proposed implementation, synthetic records, '
        'trusted scope, and fixed consent rather than two deployed architectures.',
        '',
        '## Reproducibility',
        '',
        'Run from repository root: `python part1_architecture_validation/compare_r7_controlled.py`',
        '',
        'Input fingerprints (first 12 hexadecimal characters of SHA-256):',
        '',
        f'- `models/proposed_contracts.json`: `{digest(contracts)}`',
        f'- `models/refined_variations.json`: `{digest(variations)}`',
        f'- `run_r7_variation_experiment.py`: `{digest(Path(__file__).resolve().parent / "run_r7_variation_experiment.py")}`',
        f'- `test_proposed_contracts.py`: `{digest(Path(__file__).resolve().parent / "test_proposed_contracts.py")}`',
        '',
        f'Identical case/scope/oracle checks passed for {len(test_ids)} cases across all four '
        'configurations and both model profiles.',
        '',
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv(output_dir / 'r7_controlled_comparison_summary.csv', comparison_rows)
    output_csv(output_dir / 'r7_controlled_comparison_by_case.csv', pair_rows)
    (output_dir / 'r7_controlled_comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    print('Controlled comparison verified: same I2-I4 rules, test cases, scopes and expected results.')
    print('Results:', output_dir / 'r7_controlled_comparison.md')
    return comparison_rows


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contracts', type=Path, default=base / 'models' / 'proposed_contracts.json')
    parser.add_argument('--variations', type=Path, default=base / 'models' / 'refined_variations.json')
    parser.add_argument('--coverage', type=Path, default=base / 'results' / 'reference_requirement_coverage.csv')
    parser.add_argument('--results-dir', type=Path, default=base / 'results')
    args = parser.parse_args()
    try:
        compare(args.contracts, args.variations, args.coverage, args.results_dir)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print(f'Controlled comparison failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
