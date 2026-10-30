"""Check R7 requirement -> candidate -> flow -> criterion traceability.

This validates IDs/links only. It NEVER verifies original document truth,
assessment verdict accuracy, interface semantics, or implementation coverage.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
OUT = ROOT / "results"


def read(path):
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"),
                      object_pairs_hook=reject_duplicate_keys)


def index(items, label):
    result = {}
    for entry in items:
        key = entry["id"]
        if key in result:
            raise ValueError(f"Duplicate {label}: {key}")
        result[key] = entry
    return result


def check(ok, reason):
    if not ok:
        raise ValueError(reason)


def run():
    requirements = index(read(MODELS / "requirements.json")["requirements"], "requirement")
    requirement = requirements["R7"]
    required_capabilities = index(requirement["required_capabilities"], "required capability")
    flow = next(f for f in read(MODELS / "flows.json")["flows"]
                if "R7" in f["requirement_ids"])
    steps = index(flow["steps"], "step")
    interactions = index(flow["interactions"], "interaction")
    order = read(MODELS / "components" / "_order.json")["components"]
    components = index([read(MODELS / "components" / f"{cid}.json") for cid in order], "component")
    mapping = read(MODELS / "capability_mappings.json")
    candidate_maps = index(mapping["capability_mappings"], "mapping")
    assessment = read(MODELS / "r7_reference_assessment.json")
    assessment_checks = index(assessment["checks"], "assessment check")
    assessment_capabilities = index(assessment["capabilities"], "assessed capability")

    check(assessment["requirement_id"] == flow["requirement_ids"][0] == "R7",
          "Requirement IDs do not match")
    check(set(flow["requirement_capability_ids"]) == set(required_capabilities),
          "Flow capability IDs differ from R7 requirements")
    check({m["capability_id"] for m in candidate_maps.values()} == set(required_capabilities),
          "Every R7 capability must have exactly one candidate mapping")
    check(set(assessment_capabilities) == set(required_capabilities),
          "Every R7 capability must have an assessment entry")

    # Check original flow/component references; no duplicated step mapping table.
    for step in steps.values():
        cid = step["component"]
        check(cid in components and cid in flow["participants"], f"Unknown component in {step['id']}")
        check(set(step.get("depends_on", [])) <= set(steps), f"Unknown dependency in {step['id']}")
        check(set(step.get("interaction_ids", [])) <= set(interactions), f"Unknown interaction in {step['id']}")
        behaviours = step.get("required_behaviours", [step.get("required_behaviour")])
        check(all(b in components[cid]["behaviours"] for b in behaviours),
              f"Required flow behaviour is not declared by {cid}: {step['id']}")
    pending, completed = set(steps), set()
    while pending:
        ready = {sid for sid in pending if set(steps[sid]["depends_on"]) <= completed}
        check(bool(ready), "Circular flow dependencies")
        completed.update(ready)
        pending -= ready
    for interaction in interactions.values():
        check({interaction[k] for k in ('sender','receiver','provider','consumer')} <= set(components),
              f"Unknown interface participants: {interaction['id']}")
        provider, consumer, api = interaction['provider'], interaction['consumer'], interaction['interface']
        check(api in components[provider]["provides"] and api in components[consumer]["requires"],
              f"Interface not declared by both sides: {interaction['id']}")

    for m in candidate_maps.values():
        check(m["requirement_id"] == "R7" and m["flow_id"] == flow["id"],
              f"Invalid requirement/flow link: {m['id']}")
        check(bool(m["candidate_providers"]), f"No providers in {m['id']}")
        for p in m["candidate_providers"]:
            cid, behaviour = p["component_id"], p["behaviour_id"]
            check(cid in components and cid in flow['participants'], f"Unknown candidate: {cid}")
            check(behaviour in components[cid]["behaviours"],
                  f"Behaviour {behaviour} is not declared in {cid}")
            check(p['role'] in ('primary', 'supporting'), f"Invalid candidate role: {cid}")
            check(bool(p.get('source_refs')) and all(x.strip() for x in p['source_refs']),
                  f"Missing source citations for candidate: {cid}")

    # Preserve and machine-check the four original confirmation-question links.
    questions = {}
    question_capability = {}
    for m in candidate_maps.values():
        for q in m.get('confirmation_questions', []):
            qid = q['id']
            check(qid not in questions and bool(q.get('question', '').strip()),
                  f"Duplicate or empty confirmation question: {qid}")
            questions[qid] = q['question']
            question_capability[qid] = m['capability_id']
    check(bool(questions), "Original confirmation questions are missing")
    matched_questions = set()
    for item in assessment_checks.values():
        for qid in item.get('addresses_question_ids', []):
            check(qid in questions, f"Unknown original question: {qid}")
            owning_capability = assessment_capabilities[question_capability[qid]]
            check(item['id'] in owning_capability['mandatory_checks'],
                  f"Question {qid} mapped to an unrelated criterion: {item['id']}")
            matched_questions.add(qid)
    check(matched_questions == set(questions), "An original confirmation question has no criterion link")

    direct = set()
    for capability in assessment_capabilities.values():
        ids = capability["mandatory_checks"]
        check(bool(ids) and len(ids) == len(set(ids)),
              f"Invalid mandatory checks for {capability['id']}")
        check(set(ids) <= set(assessment_checks), f"Undefined criterion in {capability['id']}")
        direct.update(ids)
    supplementary = set(assessment.get("supplementary_flow_checks", []))
    check(supplementary <= set(assessment_checks), "Undefined supplementary check")
    check(not (direct & supplementary), "Audit checks overlap with direct mandatory criteria")
    check(direct | supplementary == set(assessment_checks), "Unassigned assessment check")

    allowed = {'supported','unsupported','undetermined','not_applicable'}
    rows = []
    for check_id, item in assessment_checks.items():
        step_ids, interaction_ids = item.get('flow_step_ids', []), item.get('flow_interaction_ids', [])
        basis = item.get('traceability_basis')
        check(basis in ('r7_flow', 'scope_exclusion'), f"Missing traceability basis: {check_id}")
        check(set(step_ids) <= set(steps), f"Unknown flow step: {check_id}")
        check(set(interaction_ids) <= set(interactions), f"Unknown flow interaction: {check_id}")
        check(set(item['components']) <= set(components), f"Unknown component: {check_id}")
        check(bool(item.get('evidence_refs')), f"No cited sources: {check_id}")
        review = item['assessment']
        check(review['verdict'] in allowed and bool(review.get('rationale','').strip()),
              f"Invalid verdict/rationale: {check_id}")
        if basis == 'r7_flow':
            check(bool(step_ids or interaction_ids), f"No flow link: {check_id}")
            participants = {steps[s]['component'] for s in step_ids}
            for iid in interaction_ids:
                participants.update([interactions[iid]['sender'], interactions[iid]['receiver']])
            check(bool(set(item['components']) & participants),
                  f"Criterion components unrelated to linked flow: {check_id}")
        else:
            check(not step_ids and not interaction_ids and bool(item.get('traceability_note')),
                  f"Scope exclusion requires a note and no flow links: {check_id}")
            check(review['verdict'] == 'not_applicable',
                  f"Scope exclusion must be N/A: {check_id}")
        caps = [cid for cid, c in assessment_capabilities.items()
                if check_id in c['mandatory_checks']]
        rows.append({'criterion':check_id, 'scope':'direct' if check_id in direct else 'supplementary',
                     'capabilities':'|'.join(caps), 'components':'|'.join(item['components']),
                     'flow_steps':'|'.join(step_ids), 'interactions':'|'.join(interaction_ids),
                     'traceability_basis':basis, 'original_question_ids':'|'.join(item.get('addresses_question_ids', [])), 'recorded_verdict':review['verdict']})

    OUT.mkdir(exist_ok=True)
    with (OUT / 'traceability_links.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print('Traceability links PASSED (structural checks only).')
    print(f"R7: {len(required_capabilities)} capabilities, {len(steps)} steps, "
          f"{len(interactions)} interactions, {len(candidate_maps)} candidate mappings.")
    print(f"Assessment: {len(direct)} direct criteria, {len(supplementary)} supplementary criteria, {len(questions)} original questions linked.")
    print('Coverage and source truth NOT verified. Results: results/traceability_links.csv')


if __name__ == '__main__':
    try:
        run()
    except (ValueError, KeyError, TypeError, OSError) as err:
        raise SystemExit(f'Traceability check FAILED: {err}')
