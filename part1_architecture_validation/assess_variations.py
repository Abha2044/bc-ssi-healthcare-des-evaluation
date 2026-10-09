"""Write sourced R7 responsibility and state assessments, not coverage proofs.

This companion leaves the existing neutral validator and its results unchanged.
It does not execute C4/C6 variants or import proposed-model test passes.
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def indexed(items, label):
    result = {}
    for item in items:
        key = item['id']
        if not isinstance(key, str) or not key or key in result:
            raise ValueError(f'Invalid or duplicate {label} ID: {key}')
        result[key] = item
    return result


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def assess(model_path, results_directory):
    model = json.loads(model_path.read_text(encoding='utf-8-sig'))
    if model.get('schema_version') != '1.0' or model.get('scope') != 'R7':
        raise ValueError('Only R7 variation schema 1.0 is supported.')
    variations = indexed(model['variations'], 'variation')
    configurations = indexed(model['configurations'], 'configuration')
    checks = indexed(model['responsibility_checks'], 'responsibility')
    states = indexed(model['state_checks'], 'state')
    if not configurations or not checks or not states:
        raise ValueError('Configurations, responsibility checks and state checks are required.')
    baseline = {item['component_id']: item for item in model['baseline_evidence']}
    rows = []
    for config in configurations.values():
        selected = [variations[key] for key in config['variation_ids']]
        if len(set(config['variation_ids'])) != len(selected):
            raise ValueError('Duplicate selected variation.')
        if len({v['base_component'] for v in selected}) != len(selected):
            raise ValueError('More than one variation selected for the same component.')
        for check in checks.values():
            component = check['component_id']
            change = next((v for v in selected if v['base_component'] == component), None)
            evidence = baseline.get(component, {})
            rows.append({
                'requirement': 'R7', 'configuration': config['id'],
                'component': component, 'responsibility_check': check['id'],
                'responsibility': check['responsibility'],
                'selected_variation': change['id'] if change else '',
                'baseline_conceptual_description': evidence.get('conceptual_responsibility', ''),
                'baseline_operational_assessment': evidence.get('operational_assessment', ''),
                'baseline_operational_evidence_origin': evidence.get('evidence_origin', ''),
                'documented_change': change['change']['responsibility'] if change else '',
                'source_refs': ' | '.join(change['source_refs']) if change else evidence.get('conceptual_source', ''),
                'required_evidence': check['required_evidence'],
                'interface_compatibility': 'undetermined',
                'behaviour_test_status': 'not_assessed_for_this_configuration',
                'implementation_status': 'not_assessed',
                'coverage_status': 'undetermined',
                'reason': 'Sourced descriptions are recorded; variant execution and matching contracts are not established.'
            })
    state_rows = [{
        'requirement': 'R7', 'check': item['id'], 'information': item['information'],
        'component': item['component_id'], 'subcomponent': item['subcomponent_id'],
        'applicability': item['applicability'],
        'documented_ownership': item['documented_ownership'],
        'evidence_refs': ' | '.join(item['evidence_refs']),
        'ownership_assurance': 'documented_assignment' if item['evidence_refs'] else 'no_persistent_owner_asserted',
        'implementation_status': 'not_assessed', 'boundary': item['boundary']
    } for item in states.values()]
    results_directory.mkdir(parents=True, exist_ok=True)
    write_csv(results_directory / 'variation_assessment.csv', rows)
    write_csv(results_directory / 'state_assessment.csv', state_rows)
    print(f'R7: {len(configurations)} configurations, {len(checks)} separate responsibility checks.')
    print(f'State assessment: {len(state_rows)} entries with applicability and ownership boundaries.')
    print('This is a documentary assessment; no component variants were executed.')
    print('Compatibility and overall coverage remain undetermined.')
    print(f'Evidence tables written to: {results_directory}')


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=directory / 'models' / 'refined_variations.json')
    parser.add_argument('--results-directory', type=Path, default=directory / 'results')
    args = parser.parse_args()
    try:
        assess(args.model, args.results_directory)
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'Variation assessment stopped: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
