"""Explore assumed C4 obligation preparation and C6 enforcement availability.

This deterministic model uses supplied policy responses, not a policy evaluator.
Unavailable mechanisms and their fallback behaviours are explicit assumptions.
Results are not independent ATAM confirmation or historical baseline coverage.
Requires test_proposed_contracts.py beside this file.
"""
import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path

from test_proposed_contracts import enforce_reference, validate_response


CONFIGURATIONS = {
    'baseline': (False, False),
    'C4_star_only': (True, False),
    'C6_star_only': (False, True),
    'C4_C6_star': (True, True),
}
ASSUMPTIONS = ('block_disclosure', 'omit_obligations')


def prepare_at_c4(policy_response, available, assumption):
    """Prepare supplied obligations, or apply the assumed unavailable behaviour."""
    # Denial does not require an obligation preparation mechanism.
    if policy_response['decision'] == 'deny':
        return {'decision': 'deny', 'obligations': []}, 'deny_forwarded'
    if available or not policy_response['obligations']:
        return deepcopy(policy_response), 'obligations_prepared'
    if assumption == 'block_disclosure':
        return None, 'preparation_unavailable_blocked'
    return {'decision': 'permit', 'obligations': []}, 'preparation_unavailable_omitted'


def enforce_at_c6(response, records, available, assumption):
    if response is None:
        return {'outcome': 'preparation_blocked', 'released_records': []}, 'upstream_block'
    if response['decision'] == 'deny':
        return {'outcome': 'denied', 'released_records': []}, 'decision_enforced'
    if available:
        result, reason = enforce_reference(response, records)
        return result, reason
    if response['obligations'] and assumption == 'block_disclosure':
        return {'outcome': 'enforcement_blocked', 'released_records': []}, 'enforcement_unavailable_blocked'
    # An empty response does not reveal obligations omitted upstream.
    return {'outcome': 'permitted', 'released_records': deepcopy(records)}, 'restrictions_not_applied'


def assess_disclosure(actual, expected):
    """Use expected permitted data as an oracle, independently of variant flags."""
    released = actual['released_records']
    permitted = expected['released_records']
    allowed = {record['id']: record for record in permitted}
    prohibited = 0
    for record in released:
        allowed_record = allowed.get(record.get('id'))
        if allowed_record is None:
            prohibited += 1
        elif any(key not in allowed_record or value != allowed_record[key]
                 for key, value in record.items()):
            prohibited += 1
    # JSON equality is independent of dict field order; record order is meaningful here.
    delivery = ('not_applicable' if expected['outcome'] != 'permitted'
                else 'complete' if actual == expected else 'incomplete')
    return prohibited, delivery


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(contracts_path, results_directory):
    model = json.loads(contracts_path.read_text(encoding='utf-8-sig'))
    contracts = model['contracts']
    if len(contracts) != 1 or contracts[0]['id'] != 'CONTRACT-R7-I2':
        raise ValueError('Only CONTRACT-R7-I2 is supported.')
    contract = contracts[0]
    records = contract['test_fixture']
    tests = contract['planned_test_cases']
    if not tests or not isinstance(records, list):
        raise ValueError('Tests and a record fixture are required.')
    if len({test['id'] for test in tests}) != len(tests):
        raise ValueError('Duplicate test IDs.')
    for test in tests:
        expected = test['expected']
        if set(expected) != {'outcome', 'released_records'}:
            raise ValueError('Invalid expected-result fields.')
        if expected['outcome'] not in ('denied', 'permitted', 'enforcement_blocked'):
            raise ValueError('Unsupported expected outcome.')
        # Malformed inputs belong to the consumer reference tests. This experiment
        # accepts an unknown action to test the existing unsupported-obligation case.
        response = test['policy_response']
        if (set(response) != {'decision', 'obligations'}
                or response['decision'] not in ('permit', 'deny')
                or not isinstance(response['obligations'], list)):
            raise ValueError('This experiment needs well-shaped supplied policy decisions.')
        if any(not isinstance(o, dict) or not isinstance(o.get('action'), str)
               for o in response['obligations']):
            raise ValueError('Obligations need named actions.')
        if all(o['action'] in ('mask_fields', 'filter_date_range') for o in response['obligations']):
            validate_response(response)
    rows, summaries = [], []
    for assumption in ASSUMPTIONS:
        for configuration, (c4_available, c6_available) in CONFIGURATIONS.items():
            group = []
            for test in tests:
                response, preparation = prepare_at_c4(test['policy_response'], c4_available, assumption)
                actual, enforcement = enforce_at_c6(response, records, c6_available, assumption)
                prohibited, delivery = assess_disclosure(actual, test['expected'])
                # Fail-safe upstream blocking and consumer blocking are equivalent
                # for a case whose oracle requires no disclosure after failure.
                expected = test['expected']
                if expected['outcome'] == 'enforcement_blocked':
                    satisfied = actual['outcome'] in ('preparation_blocked', 'enforcement_blocked') and not actual['released_records']
                else:
                    satisfied = actual == expected
                row = {
                    'requirement': 'R7', 'configuration': configuration,
                    'unavailable_mechanism_assumption': assumption, 'test': test['id'],
                    'c4_preparation': preparation, 'c6_enforcement': enforcement,
                    'actual_outcome': actual['outcome'], 'released_record_count': len(actual['released_records']),
                    'prohibited_record_count': prohibited,
                    'privacy_protected_for_case': prohibited == 0,
                    'permitted_data_delivery': delivery,
                    'case_acceptance': 'PASS' if satisfied else 'FAIL',
                    'actual_result': json.dumps(actual, sort_keys=True),
                    'assessment_scope': 'assumption_based_reference_experiment',
                    'historical_baseline_coverage': 'undetermined',
                }
                rows.append(row); group.append(row)
            summary = {
                'configuration': configuration, 'assumption': assumption,
                'cases': len(group),
                'privacy_protected_cases': sum(r['privacy_protected_for_case'] for r in group),
                'permit_cases': sum(r['permitted_data_delivery'] != 'not_applicable' for r in group),
                'complete_permitted_delivery_cases': sum(r['permitted_data_delivery'] == 'complete' for r in group),
                'accepted_cases': sum(r['case_acceptance'] == 'PASS' for r in group),
                'coverage_status': 'undetermined',
                'evidence_origin': 'ATAM-informed availability assumptions plus proposed execution rules',
            }
            summaries.append(summary)
            print(f"{configuration} / {assumption}: privacy protected {summary['privacy_protected_cases']}/{len(group)}; "
                  f"complete permitted delivery {summary['complete_permitted_delivery_cases']}/{summary['permit_cases']}; "
                  f"accepted cases {summary['accepted_cases']}/{len(group)}")
    results_directory.mkdir(parents=True, exist_ok=True)
    write_csv(results_directory / 'r7_variation_experiment.csv', rows)
    write_csv(results_directory / 'r7_variation_experiment_summary.csv', summaries)
    print('Unavailable mechanisms are assumptions; this experiment does not discover baseline gaps.')
    print('Cases with expected FAIL are experimental findings, not runner errors.')
    print(f'Results written to: {results_directory}')
    return rows, summaries


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contracts', type=Path, default=directory / 'models' / 'proposed_contracts.json')
    parser.add_argument('--results-directory', type=Path, default=directory / 'results')
    args = parser.parse_args()
    try:
        run(args.contracts, args.results_directory)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'R7 variation experiment stopped: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
