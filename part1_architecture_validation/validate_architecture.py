"""Check the neutral R7 models and report separate evidence dimensions.

This pilot checks references automatically. It does not infer implementation
support from component names, or turn unanswered evidence questions into gaps.
Run it from anywhere; models and results are relative to this script.
"""

import argparse
import csv
import json
from pathlib import Path

from modelio import load_components


def read_json(path):
    """Read one JSON file and reject duplicate keys."""
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate JSON key {key}")
            result[key] = value
        return result
    with path.open(encoding="utf-8-sig") as file:
        return json.load(file, object_pairs_hook=unique_keys)


def indexed(items, label):
    """Build an ID lookup without silently dropping duplicate IDs."""
    result = {}
    for item in items:
        if item["id"] in result:
            raise ValueError(f"Duplicate {label} ID: {item['id']}")
        result[item["id"]] = item
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def documented_mapping(mapping, exact_match, evidence_key):
    """Recognize an explicitly cited design claim; do not verify source prose."""
    evidence = mapping.get(evidence_key, [])
    if isinstance(evidence, str):
        evidence = [evidence]
    cited = bool(evidence) and all(isinstance(ref, str) and ref.strip() for ref in evidence)
    if exact_match and cited and mapping.get("evidence_type") == "documented_baseline_design":
        return "documented"
    return "undetermined"


def aggregate_status(statuses):
    """Do not interpret an unresolved check as a demonstrated deficiency."""
    return "documented" if statuses and all(s == "documented" for s in statuses) else "undetermined"


def validate(models, results):
    # 1. Read the checklist, inventory, required flow and semantic mappings.
    requirements = indexed(read_json(models / "requirements.json")["requirements"], "requirement")
    components = indexed(load_components(models), "component")
    flows = indexed(read_json(models / "flows.json")["flows"], "flow")
    mappings = read_json(models / "capability_mappings.json")
    require("R7" in requirements, "R7 is missing from requirements.json.")
    r7_flows = [f for f in flows.values() if "R7" in f["requirement_ids"]]
    require(len(r7_flows) == 1, "This simple pilot requires exactly one R7 flow.")
    flow = r7_flows[0]
    capabilities = indexed(requirements["R7"]["required_capabilities"], "R7 capability")
    steps = indexed(flow["steps"], "flow step")
    interactions = indexed(flow["interactions"], "interaction")

    # 2. Check references. A broken model stops before any CSV is written.
    for component in components.values():
        for field in ("layers", "behaviours", "provides", "requires", "state"):
            for name, references in component[field].items():
                require(set(references) <= set(component["subcomponents"]),
                        f"{component['id']}: unknown subcomponent in {field}.{name}")
        require(component["state_model"] in ("stateful", "stateless", "undetermined"),
                f"{component['id']}: invalid state_model")
        require(component["state_model"] != "stateful" or bool(component["state"]),
                f"{component['id']}: stateful without state evidence")
    require(set(flow["participants"]) <= set(components), "Unknown flow participant.")
    require(set(flow["requirement_capability_ids"]) == set(capabilities),
            "R7 flow must reference all and only the R7 capabilities.")
    for step in steps.values():
        require(step["component"] in flow["participants"], f"{step['id']}: unknown participant")
        require(set(step["depends_on"]) <= set(steps), f"{step['id']}: unknown dependency")
        require(set(step.get("interaction_ids", [])) <= set(interactions),
                f"{step['id']}: unknown interaction")
    # Resolve dependencies to catch a cycle rather than assuming step order.
    completed = set()
    while len(completed) < len(steps):
        ready = {sid for sid, s in steps.items()
                 if sid not in completed and set(s["depends_on"]) <= completed}
        require(bool(ready), "Flow dependencies contain a cycle.")
        completed.update(ready)
    for interaction in interactions.values():
        require({interaction[k] for k in ("sender", "receiver", "provider", "consumer")}
                <= set(flow["participants"]), f"{interaction['id']}: unknown participant")

    capability_maps = [m for m in mappings["capability_mappings"] if m["requirement_id"] == "R7"]
    require(len({m["capability_id"] for m in capability_maps}) == len(capability_maps),
            "Duplicate R7 capability mapping.")
    require({m["capability_id"] for m in capability_maps} == set(capabilities),
            "Each R7 capability needs one mapping.")
    for mapping in capability_maps:
        require(mapping["flow_id"] == flow["id"], "Mapping references a different flow.")
        require(set(mapping["required_interaction_ids"]) <= set(interactions),
                f"{mapping['id']}: unknown interaction")
        for candidate in mapping["candidate_providers"]:
            component = components.get(candidate["component_id"])
            require(component is not None, f"{mapping['id']}: unknown component")
            require(candidate["component_id"] in flow["participants"], "Candidate outside flow.")
            require(candidate["behaviour_id"] in component["behaviours"],
                    f"{mapping['id']}: unknown candidate behaviour")

    # 3. Separate cited design responsibilities from implementation assurance.
    contributions = []
    seen = set()
    for mapping in mappings["flow_behaviour_mappings"]:
        require(mapping["step_id"] in steps, "Unknown mapped step.")
        step = steps[mapping["step_id"]]
        required = step.get("required_behaviours", [step.get("required_behaviour")])
        require(mapping["component_id"] == step["component"], "Mapped component differs from step.")
        require(mapping["required_behaviour"] in required, "Unknown required step behaviour.")
        key = (mapping["step_id"], mapping["required_behaviour"])
        require(key not in seen, "Duplicate flow behaviour mapping.")
        seen.add(key)
        component = components[mapping["component_id"]]
        require(set(mapping["candidate_behaviour_ids"]) <= set(component["behaviours"]),
                f"{mapping['step_id']}: unknown candidate behaviour")
        design_status = documented_mapping(
            mapping, mapping["required_behaviour"] in mapping["candidate_behaviour_ids"], "evidence_refs")
        contributions.append({
            "requirement": "R7", "step": mapping["step_id"],
            "component": component["id"], "required_behaviour": mapping["required_behaviour"],
            "documented_candidate_behaviours": "|".join(mapping["candidate_behaviour_ids"]),
            "state_model": component["state_model"],
            "behaviour_evidence_status": design_status,
            "evidence_refs": "|".join(mapping.get("evidence_refs", [])),
            "implementation_status": "not_assessed",
            "coverage_status": "undetermined",
            "reason": mapping["rationale"]
        })
    expected = {(sid, b) for sid, s in steps.items()
                for b in s.get("required_behaviours", [s.get("required_behaviour")])}
    require(seen == expected, "Every required step behaviour needs a mapping.")

    # 4. Validate optional source-backed interaction assessments.
    assessments = {}
    assessment_items = mappings.get("interface_assessments", [])
    indexed(assessment_items, "interface assessment")
    for assessment in assessment_items:
        require(assessment["requirement_id"] == "R7", "Interface assessment is outside the R7 pilot.")
        require(assessment["flow_id"] == flow["id"], "Interface assessment references a different flow.")
        interaction_id = assessment["interaction_id"]
        require(interaction_id in interactions, "Interface assessment references an unknown interaction.")
        require(interaction_id not in assessments, "Duplicate assessment for an interaction.")
        for field in ("evidence_refs", "documented_concepts", "unresolved_questions"):
            values = assessment[field]
            require(isinstance(values, list) and all(isinstance(v, str) and v.strip() for v in values),
                    f"{assessment['id']}: {field} must be a list of non-empty strings.")
        require(isinstance(assessment["documented_content"], str) and bool(assessment["documented_content"].strip()),
                "Interface assessment needs documented content.")
        assessments[interaction_id] = assessment

    # 5. Interface declarations and contract compatibility are different checks.
    interface_rows = []
    for item in interactions.values():
        provider = components[item["provider"]]
        consumer = components[item["consumer"]]
        provided = item["interface"] in provider["provides"]
        required = item["interface"] in consumer["requires"]
        declaration_status = "both_listed" if provided and required else "inventory_incomplete"
        assessment = assessments.get(item["id"], {})
        evidence_status = documented_mapping(assessment, bool(assessment), "evidence_refs")
        # Empty questions do not establish a contract either. This extension
        # reports source evidence; it does not infer compatible field schemas.
        contract_reason = (
            "Conceptual message content is documented; provider/consumer payload contracts remain unverified."
            if evidence_status == "documented" else
            "No source-backed interaction assessment supplied; matching interface names do not establish compatible payloads."
        )
        interface_rows.append({
            "requirement": "R7", "interaction": item["id"],
            "provider": provider["id"], "consumer": consumer["id"],
            "interface": item["interface"], "direction": item["direction"],
            "provider_interface_listed": provided,
            "consumer_interface_listed": required,
            "declaration_status": declaration_status,
            "required_fields": "|".join(item["required_payload_fields"]),
            "interaction_evidence_status": evidence_status,
            "documented_content": assessment.get("documented_content", ""),
            "documented_concepts": "|".join(assessment.get("documented_concepts", [])),
            "evidence_refs": " | ".join(assessment.get("evidence_refs", [])),
            "unresolved_questions": " | ".join(assessment.get("unresolved_questions", [])),
            "compatibility_status": "undetermined",
            "reason": (
                contract_reason
                if provided and required else
                "An interface declaration is not listed in the inventory. Review the source; this is not automatically an architectural gap."
            )
        })

    # 6. Calculate documentary support; keep contract and action checks separate.
    coverage = []
    for mapping in capability_maps:
        candidate_statuses = [
            documented_mapping(candidate,
                               candidate["behaviour_id"] == mapping["capability_id"],
                               "source_basis")
            for candidate in mapping["candidate_providers"]
        ]
        # A supporting filter is not counted as a complete obligation provider.
        provider_status = "documented" if "documented" in candidate_statuses else "undetermined"
        step_status = aggregate_status([r["behaviour_evidence_status"] for r in contributions])
        design_status = aggregate_status([provider_status, step_status])
        selected_interfaces = [r for r in interface_rows
                               if r["interaction"] in mapping["required_interaction_ids"]]
        declaration_status = (
            "both_listed" if selected_interfaces and
            all(r["declaration_status"] == "both_listed" for r in selected_interfaces)
            else "inventory_incomplete"
        )
        action_rule = mapping.get("required_action_rule")
        action_status = "not_applicable"
        if action_rule:
            require(action_rule["type"] == "at_least_one", "Unsupported action rule.")
            alternatives = set(action_rule["alternatives"])
            require(bool(alternatives), "An action rule needs alternatives.")
            required_actions = capabilities[mapping["capability_id"]].get("supported_actions", {})
            require(required_actions.get("satisfaction_rule") == action_rule["type"],
                    "Mapping action rule differs from requirement action rule.")
            require(alternatives == set(required_actions.get("alternatives", [])),
                    "Mapping actions differ from requirement actions.")
            available = {b for candidate in mapping["candidate_providers"]
                         for b in components[candidate["component_id"]]["behaviours"]}
            action_status = "listed_actions" if alternatives <= available else "undetermined"
        evidence = [ref for c in mapping["confirmation_criteria"]
                    for ref in c.get("evidence_refs", [])]
        coverage_status = "undetermined"
        coverage.append({
            "requirement": "R7", "capability": mapping["capability_id"],
            "candidate_components": "|".join(sorted({c["component_id"] for c in mapping["candidate_providers"]})),
            "documented_behaviour_status": design_status,
            "interface_declaration_status": declaration_status,
            "interface_compatibility_status": "undetermined",
            "action_inventory_status": action_status,
            "applicable_obligations_status": "undetermined" if action_rule else "not_applicable",
            "state_ownership_status": "not_assessed",
            "implementation_status": "not_assessed",
            "status": coverage_status,
            "evidence_refs": " | ".join(dict.fromkeys(evidence)),
            "reason": (
                "Cited exact behaviour mappings support documented design; compatible contracts and applicable obligation semantics are not verified."
                if design_status == "documented" else
                "Documentary support is incomplete; review behaviour mappings and source evidence."
            ),
            "questions_to_confirm": " | ".join(c["question"] for c in mapping["confirmation_criteria"])
        })
    overall = [{
        "requirement": "R7", "required_capabilities": len(capabilities),
        "documented_capabilities": sum(r["documented_behaviour_status"] == "documented" for r in coverage),
        "documented_behaviour_status": aggregate_status([r["documented_behaviour_status"] for r in coverage]),
        "confirmed_covered": sum(r["status"] == "covered" for r in coverage),
        "confirmed_missing": sum(r["status"] == "missing" for r in coverage),
        "undetermined": sum(r["status"] == "undetermined" for r in coverage),
        "classification": "undetermined",
        "scope": "Documented conceptual design, based on supplied citations; source truth, contract compatibility, state ownership and implementation are not automatically verified."
    }]
    # This extension assesses documentary mappings, not contracts or runtime
    # policy semantics. Full/partial/none still need reviewed assurance rules.
    results.mkdir(parents=True, exist_ok=True)
    for filename, rows in (
        ("component_contributions.csv", contributions),
        ("interface_validation.csv", interface_rows),
        ("capability_coverage.csv", coverage),
        ("requirement_coverage.csv", overall),
    ):
        write_csv(results / filename, rows)
    print("Model structure and references passed.")
    print(f"R7: {overall[0]['documented_capabilities']} of {len(capabilities)} capabilities have cited design mappings.")
    print("Interface compatibility and overall coverage remain undetermined.")
    print("Source statements, state ownership and implementation are not automatically verified.")
    print("Evidence tables written to:", results)


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-directory", type=Path, default=directory / "models")
    parser.add_argument("--results-directory", type=Path, default=directory / "results")
    args = parser.parse_args()
    try:
        validate(args.models_directory, args.results_directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Validation stopped: {error}\n")


if __name__ == "__main__":
    main()
