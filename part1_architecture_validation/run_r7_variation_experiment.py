"""Compare four proposed R7 realizations under common coordination rules.

Default runs include a shared-responsibility profile and an ATAM-informed
availability sensitivity profile. Neither is historical implementation evidence.
Needs the updated test_proposed_contracts.py containing derive_policy_response,
retrieve_scoped_records and enforce_with_retrieval beside this script.
"""
import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path

try:
    from test_proposed_contracts import (
        derive_policy_response, enforce_with_retrieval, reject_duplicate_keys,
        validate_response,
    )
except ImportError as error:
    raise SystemExit('Install the updated test_proposed_contracts.py beside this script: ' + str(error))


CONFIGURATIONS = {
    'baseline': (False, False),
    'C4_star_only': (True, False),
    'C6_star_only': (False, True),
    'C4_C6_star': (True, True),
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'),
                      object_pairs_hook=reject_duplicate_keys)


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def assess_disclosure(actual, expected):
    """Compare with manual expected release, separately from complete delivery."""
    allowed = {r['id']: r for r in expected['released_records']}
    prohibited = 0
    for record in actual['released_records']:
        permitted = allowed.get(record.get('id'))
        if permitted is None or any(k not in permitted or v != permitted[k]
                                    for k, v in record.items()):
            prohibited += 1
    delivery = ('not_applicable' if expected['outcome'] != 'permitted'
                else 'complete' if actual == expected else 'incomplete')
    return prohibited, delivery


def execute_case(case, source, c4_available, c6_available):
    """Shared producer/consumer meanings; only mechanism availability varies."""
    selection = case.get('selection_inputs')
    response = (derive_policy_response(selection['request'], selection['policy'], selection['consent'])
                if selection else deepcopy(case['policy_response']))
    # Validate shape while permitting the existing unsupported-action negative case.
    if (not isinstance(response, dict) or set(response) != {'decision', 'obligations'}
            or response['decision'] not in ('deny', 'permit')
            or not isinstance(response['obligations'], list)
            or any(not isinstance(o, dict) or not isinstance(o.get('action'), str)
                   for o in response['obligations'])):
        raise ValueError('Invalid policy response for ' + case['id'])
    supported = all(o['action'] in ('mask_fields', 'filter_date_range')
                    for o in response['obligations'])
    if supported:
        validate_response(response)
    trace = {'c15_called': False, 'retrieved_records': []}
    if response['decision'] == 'permit' and response['obligations'] and not c4_available:
        return ({'outcome': 'preparation_blocked', 'released_records': []}, None,
                trace, 'Assumed preparation unavailable; no disclosure.')
    if response['decision'] == 'permit' and response['obligations'] and not c6_available:
        return ({'outcome': 'enforcement_blocked', 'released_records': []}, response,
                trace, 'Assumed enforcement unavailable; no disclosure.')
    actual, trace, reason = enforce_with_retrieval(response, source, case['scope'])
    return actual, response, trace, reason


def build_cases(contract, comparison, model):
    records = deepcopy(contract['test_fixture'])
    if not records or any(not isinstance(r, dict) for r in records):
        raise ValueError('A nonempty flat-record fixture is required.')
    scope = {'allowed_record_ids': [r['id'] for r in records]}
    source = records + [deepcopy(model['proposed_retrieval_example']['extra_source_record'])]
    cases = []
    for test in contract['planned_test_cases']:
        cases.append({'id': test['id'], 'name': test['name'],
                      'policy_response': test['policy_response'],
                      'scope': deepcopy(scope), 'expected_result': test['expected']})
    cases.extend(deepcopy(comparison['additional_selection_cases']))
    ids = [c['id'] for c in cases]
    if not cases or len(ids) != len(set(ids)):
        raise ValueError('Cases must have unique IDs.')
    source_ids = [r['id'] for r in source]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError('Source record IDs must be unique.')
    for case in cases:
        expected = case['expected_result']
        if (set(expected) != {'outcome', 'released_records'}
                or expected['outcome'] not in ('permitted', 'denied', 'enforcement_blocked')
                or not isinstance(expected['released_records'], list)):
            raise ValueError('Invalid manual expectation for ' + case['id'])
        if expected['outcome'] != 'permitted' and expected['released_records']:
            raise ValueError('Denied/blocked expectations cannot release records.')
        if len({r['id'] for r in expected['released_records']}) != len(expected['released_records']):
            raise ValueError('Duplicate expected record IDs.')
        if case.get('selection_inputs'):
            validate_response(case['expected_c4_response'])
    return cases, source


def run(contracts_path, variations_path, results_directory, selected_profile='all'):
    contracts = read_json(contracts_path)['contracts']
    if len(contracts) != 1 or contracts[0]['id'] != 'CONTRACT-R7-I2':
        raise ValueError('Only CONTRACT-R7-I2 is supported.')
    model = read_json(variations_path)
    comparison = model['executable_comparison']
    if comparison['configuration_ids'] != list(CONFIGURATIONS):
        raise ValueError('Executable configuration IDs/order differ from the supported four.')
    documented = {c['id']: set(c['variation_ids']) for c in model['configurations']}
    for config, flags in CONFIGURATIONS.items():
        expected = {name for name, enabled in zip(('C4_star', 'C6_star'), flags) if enabled}
        if documented.get(config) != expected:
            raise ValueError('Configuration variation references differ: ' + config)
    profiles = comparison['profiles']
    if len({p['id'] for p in profiles}) != len(profiles) or not profiles:
        raise ValueError('Profile IDs must be unique and nonempty.')
    for profile in profiles:
        for key in ('baseline_preparation_available', 'baseline_enforcement_available'):
            if type(profile[key]) is not bool:
                raise ValueError('Availability must be a JSON Boolean.')
    if selected_profile != 'all':
        profiles = [p for p in profiles if p['id'] == selected_profile]
        if not profiles:
            raise ValueError('Unknown selected profile.')
    cases, source = build_cases(contracts[0], comparison, model)
    rows, summaries = [], []
    for profile in profiles:
        for configuration, (c4_star, c6_star) in CONFIGURATIONS.items():
            c4_available = c4_star or profile['baseline_preparation_available']
            c6_available = c6_star or profile['baseline_enforcement_available']
            group = []
            for case in cases:
                actual, response, trace, reason = execute_case(case, source, c4_available, c6_available)
                expected = case['expected_result']
                prohibited, delivery = assess_disclosure(actual, expected)
                accepted = (actual == expected or (
                    expected['outcome'] == 'enforcement_blocked'
                    and actual['outcome'] in ('preparation_blocked', 'enforcement_blocked')
                    and actual['released_records'] == []))
                selection_result = ('not_assessed_supplied_decision' if not case.get('selection_inputs')
                                    else 'PASS' if response == case['expected_c4_response'] else 'FAIL')
                if selection_result == 'FAIL':
                    accepted = False
                row = {
                    'requirement': 'R7', 'profile': profile['id'], 'configuration': configuration,
                    'profile_evidence_type': profile['evidence_type'], 'test': case['id'], 'name': case['name'],
                    'c4_preparation_available': c4_available, 'c6_enforcement_available': c6_available,
                    'c4_selection_result': selection_result,
                    'expected_c4_response': json.dumps(case.get('expected_c4_response'), sort_keys=True),
                    'actual_c4_response': json.dumps(response, sort_keys=True),
                    'actual_outcome': actual['outcome'], 'c15_called': trace['c15_called'],
                    'retrieved_records': json.dumps(trace['retrieved_records'], sort_keys=True),
                    'released_record_count': len(actual['released_records']),
                    'prohibited_record_count': prohibited, 'privacy_protected_for_case': prohibited == 0,
                    'permitted_data_delivery': delivery, 'case_acceptance': 'PASS' if accepted else 'FAIL',
                    'scope': json.dumps(case['scope'], sort_keys=True),
                    'expected_result': json.dumps(expected, sort_keys=True),
                    'actual_result': json.dumps(actual, sort_keys=True), 'reason': reason,
                    'historical_baseline_coverage': 'undetermined',
                    'assessment_scope': 'bounded_proposed_functional_realization',
                }
                rows.append(row)
                group.append(row)
            summary = {
                'profile': profile['id'], 'configuration': configuration, 'cases': len(group),
                'privacy_protected_cases': sum(r['privacy_protected_for_case'] for r in group),
                'permit_cases': sum(r['permitted_data_delivery'] != 'not_applicable' for r in group),
                'complete_permitted_delivery_cases': sum(r['permitted_data_delivery'] == 'complete' for r in group),
                'selection_cases': sum(r['c4_selection_result'] in ('PASS', 'FAIL') for r in group),
                'correct_selection_cases': sum(r['c4_selection_result'] == 'PASS' for r in group),
                'accepted_cases': sum(r['case_acceptance'] == 'PASS' for r in group),
                'coverage_status': 'not_inferred_from_test_count',
                'historical_baseline_coverage': 'undetermined',
                'evidence_origin': profile['evidence_type'], 'profile_rationale': profile['rationale'],
            }
            summaries.append(summary)
            print(f"{profile['id']} / {configuration}: accepted {summary['accepted_cases']}/{len(group)}; "
                  f"correct delivery {summary['complete_permitted_delivery_cases']}/{summary['permit_cases']}; "
                  f"privacy protected {summary['privacy_protected_cases']}/{len(group)}")
    results_directory.mkdir(parents=True, exist_ok=True)
    write_csv(results_directory / 'r7_variation_experiment.csv', rows)
    write_csv(results_directory / 'r7_variation_experiment_summary.csv', summaries)
    print('Same contracts/oracles for every configuration; availability is an explicit assumption.')
    print('Blocked permitted requests are incomplete delivery, even when privacy is protected.')
    print('This is a functional comparison, not DES, historical gap discovery or a documentary coverage update.')
    print(f'Results written to: {results_directory}')
    return rows, summaries


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contracts', type=Path, default=directory / 'models' / 'proposed_contracts.json')
    parser.add_argument('--variations', type=Path, default=directory / 'models' / 'refined_variations.json')
    parser.add_argument('--results-directory', type=Path, default=directory / 'results')
    parser.add_argument('--profile', default='all', help='all or a profile ID from the JSON')
    args = parser.parse_args()
    try:
        rows, _ = run(args.contracts, args.variations, args.results_directory, args.profile)
        # Sensitivity failures are findings. A failed shared-responsibility case
        # signals a broken proposed realization/oracle and returns a nonzero status.
        return int(any(r['profile'] == 'shared_responsibilities' and r['case_acceptance'] == 'FAIL'
                       for r in rows))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f'R7 variation experiment stopped: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
