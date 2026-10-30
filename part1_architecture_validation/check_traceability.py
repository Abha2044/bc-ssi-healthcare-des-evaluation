"""Check R7 requirement -> candidate -> flow -> criterion traceability.

Validates structural IDs, references, component declarations, and assessment
links only. It does NOT verify original document truth, assessment verdicts,
interface semantics, or implementation / requirement coverage.
"""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
OUT = ROOT / "results"


def read(path):
    """Read JSON, rejecting duplicate keys."""
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8-sig"),
        object_pairs_hook=reject_duplicate_keys,
    )


def index(items, label):
    """Index model objects by ID, rejecting duplicate IDs."""
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
    # 1. Load the R7 requirement and select exactly one R7 flow.
    requirements = index(
        read(MODELS / "requirements.json")["requirements"], "requirement"
    )
    requirement = requirements["R7"]
    required_capabilities = index(
        requirement["required_capabilities"], "required capability"
    )

    r7_flows = [
        f for f in read(MODELS / "flows.json")["flows"]
        if "R7" in f["requirement_ids"]
    ]
    check(
        len(r7_flows) == 1,
        f"Expected exactly one R7 flow, found {len(r7_flows)}",
    )
    flow = r7_flows[0]
    steps = index(flow["steps"], "step")
    interactions = index(flow["interactions"], "interaction")

    # 2. Load the component inventory BEFORE validating its references.
    order = read(MODELS / "components" / "_order.json")["components"]
    check(len(order) == len(set(order)), "Duplicate component in _order.json")
    components = index(
        [read(MODELS / "components" / f"{cid}.json") for cid in order],
        "component",
    )
    check(
        set(order) == set(components),
        "Component file ID differs from _order.json component ID",
    )

    # Preserve the original validator's subcomponent and state-model checks.
    for component in components.values():
        subcomponents = set(component["subcomponents"])
        for field in ("layers", "behaviours", "provides", "requires", "state"):
            for name, references in component[field].items():
                check(
                    set(references) <= subcomponents,
                    f"{component['id']}: unknown subcomponent in {field}.{name}",
                )

        check(
            component["state_model"] in ("stateful", "stateless", "undetermined"),
            f"{component['id']}: invalid state model",
        )
        check(
            component["state_model"] != "stateful" or bool(component["state"]),
            f"{component['id']}: stateful component without declared state",
        )

    check(
        set(flow["participants"]) <= set(components),
        "Unknown component in flow participants",
    )

    # 3. Load candidate mappings and detailed assessment.
    mapping = read(MODELS / "capability_mappings.json")
    candidate_maps = index(mapping["capability_mappings"], "mapping")
    assessment = read(MODELS / "r7_reference_assessment.json")
    assessment_checks = index(assessment["checks"], "assessment check")
    assessment_capabilities = index(assessment["capabilities"], "assessed capability")

    check(
        assessment["requirement_id"] == flow["requirement_ids"][0] == "R7",
        "Requirement IDs do not match",
    )
    check(
        set(flow["requirement_capability_ids"]) == set(required_capabilities),
        "Flow capability IDs differ from R7 requirements",
    )
    check(
        len(candidate_maps) == len(required_capabilities)
        and {m["capability_id"] for m in candidate_maps.values()}
        == set(required_capabilities),
        "Every R7 capability must have exactly one candidate mapping",
    )
    check(
        set(assessment_capabilities) == set(required_capabilities),
        "Every R7 capability must have an assessment entry",
    )

    # 4. Check required behaviours, dependencies, and flow interactions.
    for step in steps.values():
        cid = step["component"]
        check(
            cid in components and cid in flow["participants"],
            f"Unknown component in {step['id']}",
        )
        check(
            set(step.get("depends_on", [])) <= set(steps),
            f"Unknown dependency in {step['id']}",
        )
        check(
            set(step.get("interaction_ids", [])) <= set(interactions),
            f"Unknown interaction in {step['id']}",
        )
        behaviours = step.get(
            "required_behaviours", [step.get("required_behaviour")]
        )
        check(
            all(b in components[cid]["behaviours"] for b in behaviours),
            f"Required flow behaviour is not declared by {cid}: {step['id']}",
        )

    pending, completed = set(steps), set()
    while pending:
        ready = {
            sid for sid in pending
            if set(steps[sid]["depends_on"]) <= completed
        }
        check(bool(ready), "Circular flow dependencies")
        completed.update(ready)
        pending -= ready

    for interaction in interactions.values():
        participants = {
            interaction[k]
            for k in ("sender", "receiver", "provider", "consumer")
        }
        check(
            participants <= set(flow["participants"]),
            f"Interaction uses participant outside R7 flow: {interaction['id']}",
        )
        provider = interaction["provider"]
        consumer = interaction["consumer"]
        api = interaction["interface"]
        check(
            api in components[provider]["provides"]
            and api in components[consumer]["requires"],
            f"Interface not declared by both sides: {interaction['id']}",
        )

    # 5. Check nominated candidate providers and original questions.
    for m in candidate_maps.values():
        check(
            m["requirement_id"] == "R7" and m["flow_id"] == flow["id"],
            f"Invalid requirement/flow link: {m['id']}",
        )
        check(bool(m["candidate_providers"]), f"No providers in {m['id']}")
        for p in m["candidate_providers"]:
            cid, behaviour = p["component_id"], p["behaviour_id"]
            check(
                cid in components and cid in flow["participants"],
                f"Unknown candidate: {cid}",
            )
            check(
                behaviour in components[cid]["behaviours"],
                f"Behaviour {behaviour} is not declared in {cid}",
            )
            check(
                p["role"] in ("primary", "supporting"),
                f"Invalid candidate role: {cid}",
            )
            check(
                bool(p.get("source_refs"))
                and all(isinstance(x, str) and x.strip() for x in p["source_refs"]),
                f"Missing source citations for candidate: {cid}",
            )

    questions = {}
    question_capability = {}
    for m in candidate_maps.values():
        for q in m.get("confirmation_questions", []):
            qid = q["id"]
            check(
                qid not in questions and bool(q.get("question", "").strip()),
                f"Duplicate or empty confirmation question: {qid}",
            )
            questions[qid] = q["question"]
            question_capability[qid] = m["capability_id"]
    check(bool(questions), "Original confirmation questions are missing")

    matched_questions = set()
    for item in assessment_checks.values():
        for qid in item.get("addresses_question_ids", []):
            check(qid in questions, f"Unknown original question: {qid}")
            owning_capability = assessment_capabilities[question_capability[qid]]
            check(
                item["id"] in owning_capability["mandatory_checks"],
                f"Question {qid} mapped to an unrelated criterion: {item['id']}",
            )
            matched_questions.add(qid)
    check(
        matched_questions == set(questions),
        "An original confirmation question has no criterion link",
    )

    # 6. Verify criterion coverage assignments and their traceability links.
    direct = set()
    for capability in assessment_capabilities.values():
        ids = capability["mandatory_checks"]
        check(
            bool(ids) and len(ids) == len(set(ids)),
            f"Invalid mandatory checks for {capability['id']}",
        )
        check(
            set(ids) <= set(assessment_checks),
            f"Undefined criterion in {capability['id']}",
        )
        direct.update(ids)

    supplementary = set(assessment.get("supplementary_flow_checks", []))
    check(
        supplementary <= set(assessment_checks), "Undefined supplementary check"
    )
    check(
        not (direct & supplementary),
        "Audit checks overlap with direct mandatory criteria",
    )
    check(
        direct | supplementary == set(assessment_checks),
        "Unassigned assessment check",
    )

    allowed = {"supported", "unsupported", "undetermined", "not_applicable"}
    rows = []
    for check_id, item in assessment_checks.items():
        step_ids = item.get("flow_step_ids", [])
        interaction_ids = item.get("flow_interaction_ids", [])
        basis = item.get("traceability_basis")
        check(
            basis in ("r7_flow", "scope_exclusion"),
            f"Missing traceability basis: {check_id}",
        )
        check(set(step_ids) <= set(steps), f"Unknown flow step: {check_id}")
        check(
            set(interaction_ids) <= set(interactions),
            f"Unknown flow interaction: {check_id}",
        )
        check(
            set(item["components"]) <= set(components),
            f"Unknown component: {check_id}",
        )
        check(bool(item.get("evidence_refs")), f"No cited sources: {check_id}")
        review = item["assessment"]
        check(
            review["verdict"] in allowed
            and bool(review.get("rationale", "").strip()),
            f"Invalid verdict/rationale: {check_id}",
        )

        if basis == "r7_flow":
            check(bool(step_ids or interaction_ids), f"No flow link: {check_id}")
            participants = {steps[s]["component"] for s in step_ids}
            for iid in interaction_ids:
                participants.update(
                    [interactions[iid]["sender"], interactions[iid]["receiver"]]
                )
            check(
                bool(set(item["components"]) & participants),
                f"Criterion components unrelated to linked flow: {check_id}",
            )
        else:
            check(
                not step_ids
                and not interaction_ids
                and bool(item.get("traceability_note")),
                f"Scope exclusion requires a note and no flow links: {check_id}",
            )
            check(
                review["verdict"] == "not_applicable",
                f"Scope exclusion must be N/A: {check_id}",
            )

        caps = [
            cid for cid, c in assessment_capabilities.items()
            if check_id in c["mandatory_checks"]
        ]
        rows.append({
            "criterion": check_id,
            "scope": "direct" if check_id in direct else "supplementary",
            "capabilities": "|".join(caps),
            "components": "|".join(item["components"]),
            "flow_steps": "|".join(step_ids),
            "interactions": "|".join(interaction_ids),
            "traceability_basis": basis,
            "original_question_ids": "|".join(
                item.get("addresses_question_ids", [])
            ),
            "recorded_verdict": review["verdict"],
        })

    # 7. Write one structural traceability report, not a coverage verdict.
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "traceability_links.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Traceability links PASSED (structural checks only).")
    print(
        f"R7: {len(required_capabilities)} capabilities, {len(steps)} steps, "
        f"{len(interactions)} interactions, {len(candidate_maps)} candidate mappings."
    )
    print(
        f"Assessment: {len(direct)} direct criteria, "
        f"{len(supplementary)} supplementary criteria, "
        f"{len(questions)} original questions linked."
    )
    print(
        "Coverage and source truth NOT verified. "
        "Results: results/traceability_links.csv"
    )


if __name__ == "__main__":
    try:
        run()
    except (ValueError, KeyError, TypeError, OSError) as err:
        raise SystemExit(f"Traceability check FAILED: {err}")
