"""Compute reference-model coverage from explicit evidence-backed criterion reviews.

Does not verify documentary truth or derive verdicts from citations alone.
Requires r7_reference_assessment.json and refined_variations.json in models/.
Writes coverage tables, a separate audit summary, the supplied ATAM comparison, and a Markdown report. Proposed rules are not executed or automatically judged supported.
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def strings(value, label, allow_empty=True):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f'{label} must be a list of nonempty strings.')
    if len(value) != len(set(value)) or (not allow_empty and not value):
        raise ValueError(f'{label} must be nonempty when required and contain no duplicates.')
    return value


def index(items):
    if not isinstance(items, list):
        raise ValueError('Model collections must be lists of objects.')
    result = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Each model entry must be an object.')
        key = item['id']
        if not isinstance(key, str) or not key.strip() or key in result:
            raise ValueError(f'Invalid or duplicate ID: {key}')
        result[key] = item
    return result


def classification(verdicts):
    applicable = [v for v in verdicts if v != 'not_applicable']
    if not applicable or 'undetermined' in applicable:
        return 'undetermined'
    if all(v == 'supported' for v in applicable):
        return 'full'
    if all(v == 'unsupported' for v in applicable):
        return 'none'
    return 'partial'


def review(check, configuration):
    assessment = check.get('configuration_overrides', {}).get(configuration, check['assessment'])
    if not isinstance(assessment, dict):
        raise ValueError(f"Assessment must be an object: {check['id']}")
    verdict = assessment['verdict']
    if verdict not in {'supported', 'unsupported', 'undetermined', 'not_applicable'}:
        raise ValueError(f"Invalid verdict for {check['id']}")
    refs = assessment.get('supporting_evidence_refs', [])
    strings(refs, f"Review evidence for {check['id']}")
    for field in ('assessed_by', 'rationale'):
        if not isinstance(assessment.get(field, ''), str):
            raise ValueError(f"{field} must be text: {check['id']}")
    if verdict != 'undetermined':
        if not assessment.get('assessed_by', '').strip() or not assessment.get('rationale', '').strip() or not refs:
            raise ValueError(f"A determined verdict requires assessor, rationale and evidence: {check['id']}")
    return assessment


def write(path, rows):
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def cell(value):
    """Escape input text for readable Markdown table cells."""
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def table(headers, rows):
    lines = ['| ' + ' | '.join(map(cell, headers)) + ' |',
             '| ' + ' | '.join('---' for _ in headers) + ' |']
    lines.extend('| ' + ' | '.join(map(cell, row)) + ' |' for row in rows)
    return '\n'.join(lines)


def component_comparison(variations, criterion_rows, summary_rows):
    """Render sourced descriptions and actual review outcomes; never assign verdicts."""
    baselines = {entry["component_id"]: entry
                 for entry in variations.get("baseline_evidence", [])}
    variants = {entry["id"]: entry for entry in variations.get("variations", [])}
    columns = [("C4", None, "baseline"), ("C4", "C4_star", "C4_star_only"),
               ("C6", None, "baseline"), ("C6", "C6_star", "C6_star_only")]
    summaries = {row["configuration"]: row for row in summary_rows}
    rows = []
    for aspect in ("Behaviour", "Architectural difference", "Interfaces",
                   "State", "Remaining uncertainty", "Configuration coverage", "Source basis"):
        values = []
        for component, variant_id, configuration in columns:
            base = baselines.get(component, {})
            variant = variants.get(variant_id, {}) if variant_id else {}
            selected = [row for row in criterion_rows
                        if row["configuration"] == configuration
                        and component in row["components"].split("|")]
            if aspect == "Behaviour":
                value = (variant.get("change", {}).get("responsibility") if variant_id
                         else base.get("conceptual_responsibility"))
            elif aspect == "Architectural difference":
                if variant_id:
                    change = variant.get("change", {})
                    value = " / ".join(str(change[k]) for k in
                                       ("type", "subcomponent_id", "name") if change.get(k))
                    value += ". " + variant.get("boundary", "")
                else:
                    value = base.get("operational_assessment", "")
                    if value:
                        value += " Reported origin: " + base.get("evidence_origin", "unspecified")
            elif aspect == "Interfaces":
                if variant_id:
                    value = variant.get("interface_effect")
                else:
                    value = " / ".join(row["criterion"] for row in selected
                                       if row["kind"] == "interface")
                    value = ("Required interaction criteria (compatibility assessed separately): " + value
                             if value else None)
            elif aspect == "State":
                if variant_id:
                    value = variant.get("state_effect")
                else:
                    entries = [entry for entry in variations.get("state_checks", [])
                               if entry.get("component_id") == component]
                    value = " / ".join(entry["information"] + ": "
                                       + entry.get("documented_ownership", "Not specified")
                                       + " " + entry.get("boundary", "") for entry in entries)
            elif aspect == "Remaining uncertainty":
                value = " / ".join(row["check"] + ": " + row["open_questions"]
                                   for row in selected if row["verdict"] == "undetermined")
                if not value:
                    value = "No unresolved assigned checks in this recorded review; implementation is not assessed."
            elif aspect == "Configuration coverage":
                summary = summaries.get(configuration)
                value = (f"{configuration}: {summary['coverage']} "
                         f"({summary['supported_checks']} supported, "
                         f"{summary['unresolved_checks']} unresolved). Whole configuration, not component-alone coverage."
                         if summary else None)
            else:
                refs = (variant.get("source_refs", []) if variant_id else
                        [base.get("conceptual_source", ""), base.get("operational_source", "")])
                if not variant_id:
                    refs += [ref for entry in variations.get("state_checks", [])
                             if entry.get("component_id") == component
                             for ref in entry.get("evidence_refs", [])]
                value = " / ".join(dict.fromkeys(ref for ref in refs if ref))
            values.append(value or "Not specified in the supplied variation model.")
        rows.append([aspect] + values)
    return table(["Aspect", "C4 baseline", "C4* refined", "C6 baseline", "C6* refined"], rows)


def write_report(path, model, variations, configurations, criterion_rows, component_rows, capability_rows, summary_rows, audit_rows, atam_rows):
    lines = [
        '# R7 reference-architecture assessment', '',
        'This report assesses the conceptual reference architecture using explicit criterion reviews. '
        'It does not infer a verdict from a citation or execute the component variants.', '',
        '## Coverage rules', '',
        'Full: all applicable mandatory checks are supported. Partial: supported and unsupported '
        'checks coexist with no unresolved checks. None: all applicable checks are unsupported. '
        'Any unresolved mandatory check, or no applicable checks, leaves coverage undetermined. '
        'Direct R7 coverage uses capability checks only. Supplementary audit is reported separately. '
        'Proposed-design results must not be interpreted as historical baseline evidence.', '',
        '## Baseline-versus-refined component comparison', '',
        'Descriptions come from refined_variations.json; interface criteria and uncertainty come '
        'from the recorded reviews. Appendix A operational findings retain their ATAM-derived origin. '
        'This table does not infer missing behaviour from a missing subcomponent name.', '',
        component_comparison(variations, criterion_rows, summary_rows), '',
        'C4* and C6* columns describe each individual replacement. The combined configuration '
        'is assessed in the results below. The separately labelled proposed logical design '
        'contains additional rules and must not be treated as evidence of a refinement-only improvement.', '',
        '## Configuration results', '',
        table(['Configuration', 'Evidence type', 'Coverage', 'Supported', 'Unsupported', 'Unresolved', 'Not applicable'],
              [[r['configuration'], r['configuration_evidence_type'], r['coverage'], r['supported_checks'], r['unsupported_checks'],
                r['unresolved_checks'], r['not_applicable_checks']] for r in summary_rows]), '',
        'Reviews are inherited from the shared assessment unless an explicit configuration override '
        'is supplied. Identical results therefore do not establish that baseline and refined implementations behave identically.', '',
        '## Capability coverage', '',
        table(['Configuration', 'Capability', 'Coverage', 'Unresolved checks'],
              [[r['configuration'], r['capability'], r['coverage'], r['unresolved_checks'] or 'None']
               for r in capability_rows]), '',
        '## Individual component contributions', '',
        'Each result concerns that component’s assigned checks, not its ability to satisfy all of R7 alone.', '',
        table(['Configuration', 'Component', 'Contribution coverage', 'Unresolved checks'],
              [[r['configuration'], r['component'], r['contribution_coverage'], r['unresolved_checks']]
               for r in component_rows]), '',
        '## Reviewed criteria and evidence', ''
    ]
    if audit_rows:
        lines += ['## Supporting audit completeness', '',
                  'These checks do not determine direct R7 coverage.', '',
                  table(['Configuration', 'Evidence type', 'Coverage', 'Unresolved checks'],
                        [[r['configuration'], r['configuration_evidence_type'], r['coverage'], r['unresolved_checks']]
                         for r in audit_rows]), '']
    if atam_rows:
        lines += ['## Separate ATAM comparison', '',
                  'This supplied interpretation is not independently reproduced gap evidence.', '',
                  table(['ATAM gap', 'Interpretation'],
                        [[r['gap'], r['interpretation']] for r in atam_rows]), '']
    for configuration in configurations:
        lines += [f'### {cell(configuration)}', '',
                  table(['Check', 'Kind', 'Verdict', 'Review origin', 'Rationale', 'Review evidence', 'Open questions'],
                        [[r['check'], r['kind'], r['verdict'], r['assessment_origin'], r['rationale'],
                          r['review_evidence_refs'], r['open_questions'] if r['verdict'] == 'undetermined' else '']
                         for r in criterion_rows if r['configuration'] == configuration]), '']
    lines += ['## Interpretation', '',
              'Resolve open criteria through cited source review or an explicitly identified proposed design. '
              'A proposed contract can support a proposed variation; it does not establish historical baseline compatibility. '
              'Unknown state ownership should be assessed only where the selected behaviour requires retained state. '
              'ATAM alignment and operational experiment results remain separate from this coverage calculation.', '',
              'Implementation assurance: not assessed. Source truth and assessor judgments are not automatically verified.', '']
    path.write_text('\n'.join(lines), encoding='utf-8')


def run(models, results):
    model = read_json(models / 'r7_reference_assessment.json')
    variations = read_json(models / 'refined_variations.json')
    if not isinstance(model, dict) or not isinstance(variations, dict):
        raise ValueError('Both model files must contain JSON objects.')
    if model.get('schema_version') != '1.0' or model.get('requirement_id') != 'R7':
        raise ValueError('Only R7 assessment schema 1.0 is supported.')
    if model.get('assessment_target') != 'conceptual_reference_architecture':
        raise ValueError('Wrong assessment target.')
    checks = index(model['checks']); capabilities = index(model['capabilities'])
    configurations = index(variations['configurations'])
    variants = index(variations['variations'])
    if not checks or not capabilities or not configurations:
        raise ValueError('Checks, capabilities and configurations are required.')
    for config in configurations.values():
        evidence_type = config.get('evidence_type', 'documented_reference_design')
        if evidence_type not in {'documented_reference_design', 'documented_baseline_design', 'atam_derived_refinement', 'proposed_design'}:
            raise ValueError(f"Invalid evidence type: {config['id']}")
        rules_ref = config.get('logical_rules_ref')
        if rules_ref and (evidence_type != 'proposed_design' or not isinstance(variations.get(rules_ref), dict)):
            raise ValueError(f"Invalid proposed rule reference: {config['id']}")
        selected_components = []
        for variant_id in strings(config['variation_ids'], f"Variation IDs for {config['id']}"):
            if variant_id not in variants:
                raise ValueError(f'Unknown variation: {variant_id}')
            selected_components.append(variants[variant_id]['base_component'])
        if len(selected_components) != len(set(selected_components)):
            raise ValueError('A configuration selects multiple variations for one component.')
    for check in checks.values():
        if check['kind'] not in ('behaviour', 'interface', 'state'):
            raise ValueError(f"Invalid check: {check['id']}")
        strings(check['components'], f"Components for {check['id']}", allow_empty=False)
        strings(check['evidence_refs'], f"Source references for {check['id']}")
        strings(check['open_questions'], f"Open questions for {check['id']}")
        if not isinstance(check['criterion'], str) or not check['criterion'].strip():
            raise ValueError(f"Criterion must be nonempty text: {check['id']}")
        if not isinstance(check.get('configuration_overrides', {}), dict):
            raise ValueError(f"Configuration overrides must be an object: {check['id']}")
        if set(check.get('configuration_overrides', {})) - set(configurations):
            raise ValueError('Override names an unknown configuration.')
    if strings(model.get('supporting_flow_checks', []), 'Supporting flow checks'):
        raise ValueError('Move supplementary audit checks to supplementary_flow_checks; direct R7 coverage uses capability checks only.')
    supplementary = strings(model.get('supplementary_flow_checks', []), 'Supplementary flow checks')
    if set(supplementary) - set(checks):
        raise ValueError('Unknown supplementary check.')
    required = set()
    for capability in capabilities.values():
        required.update(strings(capability['mandatory_checks'],
                                f"Mandatory checks for {capability['id']}", allow_empty=False))
    if required - set(checks):
        raise ValueError(f'Unknown checks: {sorted(required - set(checks))}')
    criterion_rows, component_rows, capability_rows, summary_rows, audit_rows = [], [], [], [], []
    atam_rows = []
    for entry in model.get('atam_comparison', []):
        atam_rows.append({'gap': entry.get('gap') or '',
                          'interpretation': entry['interpretation'],
                          'assessment_scope': 'documentary_interpretation_not_independent_gap_reproduction'})
    for configuration in configurations:
        evidence_type = configurations[configuration].get('evidence_type', 'documented_reference_design')
        assessments = {key: review(check, configuration) for key, check in checks.items()}
        for key, check in checks.items():
            assessed = assessments[key]
            criterion_rows.append({
                'configuration': configuration, 'configuration_evidence_type': evidence_type, 'check': key, 'kind': check['kind'],
                'components': '|'.join(check['components']), 'criterion': check['criterion'],
                'verdict': assessed['verdict'], 'assessed_by': assessed.get('assessed_by', ''),
                'assessment_origin': ('configuration_override' if configuration in check.get('configuration_overrides', {}) else 'shared_assessment'),
                'rationale': assessed.get('rationale', ''),
                'source_refs': ' | '.join(check['evidence_refs']),
                'review_evidence_refs': ' | '.join(assessed.get('supporting_evidence_refs', [])),
                'open_questions': ' | '.join(assessed.get('open_questions', check['open_questions']))
            })
        for component in sorted({c for check in checks.values() for c in check['components']}):
            ids = [key for key, check in checks.items() if component in check['components']]
            component_rows.append({
                'configuration': configuration, 'configuration_evidence_type': evidence_type, 'component': component,
                'contribution_coverage': (
                    'not_applicable'
                    if all(assessments[key]['verdict'] == 'not_applicable'
                           for key in ids)
                    else classification([assessments[key]['verdict'] for key in ids])
                ),
                'criterion_ids': '|'.join(ids),
                'supported_checks': sum(assessments[key]['verdict'] == 'supported' for key in ids),
                'unsupported_checks': sum(assessments[key]['verdict'] == 'unsupported' for key in ids),
                'unresolved_checks': sum(assessments[key]['verdict'] == 'undetermined' for key in ids),
                'scope': 'assigned contribution, not whole R7 satisfaction'
            })
        for capability in capabilities.values():
            ids = capability['mandatory_checks']
            capability_rows.append({
                'configuration': configuration, 'configuration_evidence_type': evidence_type, 'requirement': 'R7', 'capability': capability['id'],
                'coverage': classification([assessments[key]['verdict'] for key in ids]),
                'unresolved_checks': '|'.join(key for key in ids if assessments[key]['verdict'] == 'undetermined'),
                'unsupported_checks': '|'.join(key for key in ids if assessments[key]['verdict'] == 'unsupported'),
            })
        verdicts = [assessments[key]['verdict'] for key in sorted(required)]
        row = {
            'configuration': configuration, 'configuration_evidence_type': evidence_type, 'requirement': 'R7',
            'assessment_target': model['assessment_target'],
            'coverage': classification(verdicts),
            'supported_checks': verdicts.count('supported'),
            'unsupported_checks': verdicts.count('unsupported'),
            'unresolved_checks': verdicts.count('undetermined'),
            'not_applicable_checks': verdicts.count('not_applicable'),
            'implementation_assurance': 'not_assessed',
        }
        summary_rows.append(row)
        if supplementary:
            audit_verdicts = [assessments[key]['verdict'] for key in supplementary]
            audit_rows.append({
                'configuration': configuration, 'configuration_evidence_type': evidence_type,
                'requirement': 'R7', 'scope': 'supporting audit; excluded from direct R7 coverage',
                'coverage': classification(audit_verdicts),
                'supported_checks': audit_verdicts.count('supported'),
                'unsupported_checks': audit_verdicts.count('unsupported'),
                'not_applicable_checks': audit_verdicts.count('not_applicable'),
                'unresolved_checks': '|'.join(key for key in supplementary if assessments[key]['verdict'] == 'undetermined'),
            })
        print(f"{configuration} [{evidence_type}]: {row['coverage']} ({row['supported_checks']} supported, "
              f"{row['unsupported_checks']} unsupported, {row['unresolved_checks']} unresolved)")
    results.mkdir(parents=True, exist_ok=True)
    for name, rows in (
        ('reference_criterion_assessment.csv', criterion_rows),
        ('reference_component_coverage.csv', component_rows),
        ('reference_capability_coverage.csv', capability_rows),
        ('reference_requirement_coverage.csv', summary_rows),
    ):
        write(results / name, rows)
    if audit_rows:
        write(results / 'reference_supporting_flow_coverage.csv', audit_rows)
    if atam_rows:
        write(results / 'atam_comparison.csv', atam_rows)
    write_report(results / 'r7_reference_architecture_report.md', model, variations, configurations,
                 criterion_rows, component_rows, capability_rows, summary_rows, audit_rows, atam_rows)
    print('Coverage is computed from explicit criterion reviews; source truth is not automatically verified.')
    print(f'Results written to: {results}')


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models-directory', type=Path, default=directory / 'models')
    parser.add_argument('--results-directory', type=Path, default=directory / 'results')
    args = parser.parse_args()
    try:
        run(args.models_directory, args.results_directory)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'Reference assessment stopped: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
