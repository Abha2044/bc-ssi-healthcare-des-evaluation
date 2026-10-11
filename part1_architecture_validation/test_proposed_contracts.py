"""Execute the proposed R7 reference model, not actual C4/C6 services.

Rules are implemented explicitly below; expected results come from JSON.
This runner does not interpret arbitrary contract prose or infer baseline coverage.
"""

import argparse
import csv
import json
import re
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date must use YYYY-MM-DD.")
    return date.fromisoformat(value)


def validate_response(response):
    """Reject unsupported/malformed payloads before any data is released."""
    if not isinstance(response, dict) or set(response) != {"decision", "obligations"}:
        raise ValueError("Response must contain only decision and obligations.")
    if response["decision"] not in ("permit", "deny"):
        raise ValueError("Invalid decision.")
    obligations = response["obligations"]
    if not isinstance(obligations, list):
        raise ValueError("Obligations must be an array.")
    for obligation in obligations:
        if not isinstance(obligation, dict):
            raise ValueError("Each obligation must be an object.")
        action = obligation.get("action")
        if action == "mask_fields":
            if set(obligation) != {"action", "fields"}:
                raise ValueError("Invalid mask_fields fields.")
            fields = obligation["fields"]
            if (not isinstance(fields, list) or not fields
                    or any(not isinstance(f, str) or not f.strip() for f in fields)):
                raise ValueError("Mask targets must be a nonempty array of names.")
            if len(fields) != len(set(fields)):
                raise ValueError("Mask targets must be unique.")
        elif action == "filter_date_range":
            if set(obligation) != {"action", "field", "from", "to"}:
                raise ValueError("Invalid filter_date_range fields.")
            if not isinstance(obligation["field"], str) or not obligation["field"].strip():
                raise ValueError("Date field must be a nonempty name.")
            if parse_date(obligation["from"]) > parse_date(obligation["to"]):
                raise ValueError("Date bounds are reversed.")
        else:
            raise ValueError("Unsupported obligation action.")


def enforce_reference(response, records):
    """Return only a complete permitted result, or no records on failure."""
    try:
        validate_response(response)
        if response["decision"] == "deny":
            return {"outcome": "denied", "released_records": []}, "Policy denied access."
        if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
            raise ValueError("Fixture must be an array of model records.")
        result = deepcopy(records)
        filters = [o for o in response["obligations"] if o["action"] == "filter_date_range"]
        masks = [o for o in response["obligations"] if o["action"] == "mask_fields"]
        # Validate all required date values before processing any filters.
        for obligation in filters:
            for record in result:
                parse_date(record.get(obligation["field"]))
        for obligation in filters:
            lower, upper = parse_date(obligation["from"]), parse_date(obligation["to"])
            result = [r for r in result if lower <= parse_date(r[obligation["field"]]) <= upper]
        for obligation in masks:
            for record in result:
                for field in obligation["fields"]:
                    record.pop(field, None)
        return {"outcome": "permitted", "released_records": result}, "All supplied obligations applied."
    except ValueError as error:
        return {"outcome": "enforcement_blocked", "released_records": []}, str(error)


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def derive_policy_response(request, policy, consent):
    """Proposed C4 model for this flat-record example, not a general PDP."""
    required = (
        (request, {"role", "action", "resource", "purpose"}),
        (policy, {"permit_role", "permit_action", "permit_purpose", "prohibited_fields"}),
        (consent, {"access_permitted", "record_date_from", "record_date_to"}),
    )
    for value, keys in required:
        if not isinstance(value, dict) or set(value) != keys:
            raise ValueError("Selection example has missing or unsupported input fields.")
    if any(not isinstance(value, str) or not value.strip() for value in request.values()):
        raise ValueError("Request fields must be nonempty strings.")
    for key in ("permit_role", "permit_action", "permit_purpose"):
        if not isinstance(policy[key], str) or not policy[key].strip():
            raise ValueError("Policy matching fields must be nonempty strings.")
    if request["resource"] != "clinical_records":
        raise ValueError("This proposed selection model supports clinical_records only.")
    if type(consent["access_permitted"]) is not bool:
        raise ValueError("Consent permission must be a Boolean.")
    fields = policy["prohibited_fields"]
    if (not isinstance(fields, list)
            or any(not isinstance(field, str) or not field.strip() for field in fields)
            or len(fields) != len(set(fields))):
        raise ValueError("Prohibited fields must be unique nonempty names.")
    lower = parse_date(consent["record_date_from"])
    upper = parse_date(consent["record_date_to"])
    if lower > upper:
        raise ValueError("Consent date bounds are reversed.")
    permitted = (
        consent["access_permitted"]
        and request["role"] == policy["permit_role"]
        and request["action"] == policy["permit_action"]
        and request["purpose"] == policy["permit_purpose"]
    )
    if not permitted:
        return {"decision": "deny", "obligations": []}
    obligations = []
    if fields:
        obligations.append({"action": "mask_fields", "fields": list(fields)})
    obligations.append({
        "action": "filter_date_range", "field": "record_date",
        "from": consent["record_date_from"], "to": consent["record_date_to"],
    })
    return {"decision": "permit", "obligations": obligations}


def run_selection_example(variations_path, contract_path, output_path):
    """Compare derived C4 output and C6 release against hand-written expectations."""
    def read(path):
        return json.loads(path.read_text(encoding="utf-8-sig"),
                          object_pairs_hook=reject_duplicate_keys)

    example = read(variations_path)["proposed_selection_example"]
    contracts = read(contract_path)["contracts"]
    if len(contracts) != 1 or contracts[0]["id"] != "CONTRACT-R7-I2":
        raise ValueError("Selection test requires CONTRACT-R7-I2.")
    contract = contracts[0]
    # R7-T5 is the existing manually specified combined-transformation oracle.
    oracles = [test for test in contract["planned_test_cases"] if test["id"] == "R7-T5"]
    if len(oracles) != 1:
        raise ValueError("Selection test requires exactly one R7-T5 expected result.")
    oracle = oracles[0]
    expected_response = example["expected_c4_response"]
    validate_response(expected_response)
    if expected_response != oracle["policy_response"]:
        raise ValueError("Selection example and R7-T5 describe different expectations.")
    actual_response = derive_policy_response(
        example["request"], example["fixed_policy"], example["fixed_consent"])
    actual, reason = enforce_reference(actual_response, contract["test_fixture"])
    selection_passed = actual_response == expected_response
    delivery_passed = actual == oracle["expected"]
    passed = selection_passed and delivery_passed
    row = {
        "test": "R7-T6", "example": example["id"],
        "configuration": "R7_proposed_logical_design",
        "name": "Derive obligations from policy and consent, then enforce them",
        "selection_result": "PASS" if selection_passed else "FAIL",
        "delivery_result": "PASS" if delivery_passed else "FAIL",
        "result": "PASS" if passed else "FAIL",
        "expected_c4_response": json.dumps(expected_response, sort_keys=True),
        "actual_c4_response": json.dumps(actual_response, sort_keys=True),
        "expected_result": json.dumps(oracle["expected"], sort_keys=True),
        "actual_result": json.dumps(actual, sort_keys=True), "reason": reason,
        "assessment_scope": "one_proposed_policy_consent_example",
        "limitations": "Synthetic flat records; no C15 service, general policy engine, consent updates or independent implementations assessed.",
        "baseline_interface_compatibility": "undetermined",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    print(f"R7-T6: {row['result']} - {row['name']}")
    print(f"C4 selection: {row['selection_result']}; C6 delivery: {row['delivery_result']}")
    print("This tests one proposed example; it does not change documentary coverage verdicts.")
    print(f"Selection results written to: {output_path}")
    return 0 if passed else 1


def retrieve_scoped_records(records, scope, obligations):
    """Proposed C15: ID allow-list plus delegated inclusive date filters.

    Scope is a trusted, explicitly supplied fixture input, not computed by C15.
    This models neither a real FHIR endpoint nor patient/consent authorization.
    """
    if not isinstance(scope, dict) or set(scope) != {"allowed_record_ids"}:
        raise ValueError("Scope requires an explicit record-ID allow-list.")
    ids = scope["allowed_record_ids"]
    if (not isinstance(ids, list)
            or any(not isinstance(i, str) or not i.strip() for i in ids)
            or len(ids) != len(set(ids))):
        raise ValueError("Scope IDs must be unique nonempty strings.")
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        raise ValueError("C15 requires flat model records.")
    record_ids = [r.get("id") for r in records]
    if (any(not isinstance(i, str) or not i.strip() for i in record_ids)
            or len(record_ids) != len(set(record_ids))):
        raise ValueError("Source record IDs must be unique nonempty strings.")
    validate_response({"decision": "permit", "obligations": obligations})
    scoped = [deepcopy(r) for r in records if r["id"] in ids]
    for obligation in obligations:
        if obligation["action"] != "filter_date_range":
            continue  # Masking belongs to C6 in this proposed allocation.
        lower, upper = parse_date(obligation["from"]), parse_date(obligation["to"])
        for record in scoped:
            parse_date(record.get(obligation["field"]))
        scoped = [r for r in scoped
                  if lower <= parse_date(r[obligation["field"]]) <= upper]
    return scoped


def enforce_with_retrieval(response, source_records, scope):
    """C6 validates/denies first, calls proposed C15, then enforces all obligations."""
    trace = {"c15_called": False, "retrieved_records": []}
    try:
        validate_response(response)
        if response["decision"] == "deny":
            return {"outcome": "denied", "released_records": []}, trace, "Denied before retrieval."
        trace["c15_called"] = True
        retrieved = retrieve_scoped_records(source_records, scope, response["obligations"])
        trace["retrieved_records"] = deepcopy(retrieved)
        actual, reason = enforce_reference(response, retrieved)
        return actual, trace, reason
    except ValueError as error:
        return {"outcome": "enforcement_blocked", "released_records": []}, trace, str(error)


def run_retrieval_examples(variations_path, contract_path, output_path):
    """I3 cases use explicit expected C15 and final outputs, not generated oracles."""
    def read(path):
        return json.loads(path.read_text(encoding="utf-8-sig"),
                          object_pairs_hook=reject_duplicate_keys)
    example = read(variations_path)["proposed_selection_example"]
    contract = read(contract_path)["contracts"][0]
    response = derive_policy_response(example["request"], example["fixed_policy"],
                                      example["fixed_consent"])
    # Recent but unauthorized record: date filtering alone MUST NOT admit it.
    source = deepcopy(contract["test_fixture"]) + [{
        "id": "record-other", "record_date": "2026-09-20",
        "address": "Excluded synthetic address", "clinical_summary": "Out of scope"
    }]
    expected_retrieved = [{"id": "record-2", "record_date": "2026-09-20",
                           "address": "Synthetic address B",
                           "clinical_summary": "Recent synthetic record"}]
    expected_release = [{"id": "record-2", "record_date": "2026-09-20",
                         "clinical_summary": "Recent synthetic record"}]
    cases = [
        ("R7-T7", "C15 restricts scope/dates; C6 masks before release", response,
         {"allowed_record_ids": ["record-1", "record-2"]}, True,
         expected_retrieved, {"outcome": "permitted", "released_records": expected_release}),
        ("R7-T8", "Deny prevents C15 retrieval", {"decision": "deny", "obligations": []},
         {"allowed_record_ids": ["record-1", "record-2"]}, False, [],
         {"outcome": "denied", "released_records": []}),
        ("R7-T9", "Missing explicit scope blocks disclosure", response, {}, True, [],
         {"outcome": "enforcement_blocked", "released_records": []}),
        ("R7-T10", "Empty authorized scope releases no records", response,
         {"allowed_record_ids": []}, True, [],
         {"outcome": "permitted", "released_records": []}),
    ]
    rows = []
    for test, name, policy_response, scope, called, retrieved, expected in cases:
        actual, trace, reason = enforce_with_retrieval(policy_response, source, scope)
        passed = (actual == expected and trace["c15_called"] == called
                  and trace["retrieved_records"] == retrieved)
        rows.append({
            "test": test, "name": name, "configuration": "R7_proposed_logical_design",
            "result": "PASS" if passed else "FAIL",
            "scope": json.dumps(scope, sort_keys=True),
            "expected_c15_called": called, "actual_c15_called": trace["c15_called"],
            "expected_retrieved_records": json.dumps(retrieved, sort_keys=True),
            "actual_retrieved_records": json.dumps(trace["retrieved_records"], sort_keys=True),
            "expected_result": json.dumps(expected, sort_keys=True),
            "actual_result": json.dumps(actual, sort_keys=True), "reason": reason,
            "assessment_scope": "proposed_I3_flat_record_allocation",
            "limitations": "Trusted scope fixture; no actual FHIR, patient binding, scope derivation or independent services tested. No automatic coverage update."
        })
        print(f"{test}: {rows[-1]['result']} - {name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Proposed I3 results written to: {output_path}")
    print("C15 applies ID scope and date bounds; C6 applies masking and rechecks date obligations.")
    print("Historical baseline and documentary coverage verdicts are unchanged.")
    return 0 if all(r["result"] == "PASS" for r in rows) else 1


def run(contract_path, output_path):
    model = json.loads(contract_path.read_text(encoding="utf-8-sig"),
                       object_pairs_hook=reject_duplicate_keys)
    if model.get("schema_version") != "1.0":
        raise ValueError("Only proposed contract schema 1.0 is supported.")
    contracts = model.get("contracts", [])
    if len(contracts) != 1 or contracts[0].get("id") != "CONTRACT-R7-I2":
        raise ValueError("This runner supports only CONTRACT-R7-I2.")
    contract = contracts[0]
    fixture = contract["test_fixture"]
    tests = contract["planned_test_cases"]
    if not isinstance(tests, list) or not tests:
        raise ValueError("No planned test cases supplied.")
    rows, seen = [], set()
    for test in tests:
        test_id = test["id"]
        if not isinstance(test_id, str) or not test_id or test_id in seen:
            raise ValueError("Test IDs must be nonempty and unique.")
        seen.add(test_id)
        expected = test["expected"]
        if (not isinstance(expected, dict)
                or set(expected) != {"outcome", "released_records"}
                or expected["outcome"] not in ("denied", "permitted", "enforcement_blocked")
                or not isinstance(expected["released_records"], list)):
            raise ValueError(f"Invalid expected result for {test_id}.")
        actual, reason = enforce_reference(test["policy_response"], fixture)
        passed = actual == expected
        rows.append({
            "contract": contract["id"], "requirement": contract["requirement_id"],
            "test": test_id, "name": test["name"],
            "expected_outcome": expected["outcome"], "actual_outcome": actual["outcome"],
            "expected_result": json.dumps(expected, sort_keys=True),
            "actual_result": json.dumps(actual, sort_keys=True),
            "result": "PASS" if passed else "FAIL", "reason": reason,
            "assessment_scope": "proposed_reference_model",
            "baseline_interface_compatibility": "undetermined",
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(f"{row['test']}: {row['result']} - {row['name']}")
    passed_count = sum(row["result"] == "PASS" for row in rows)
    print(f"Proposed reference-model tests: {passed_count}/{len(rows)} passed.")
    print("Historical baseline compatibility and overall R7 coverage remain undetermined.")
    print(f"Results written to: {output_path}")
    return 0 if passed_count == len(rows) else 1


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path,
                        default=directory / "models" / "proposed_contracts.json")
    parser.add_argument("--output", type=Path,
                        default=directory / "results" / "proposed_contract_test_results.csv")
    parser.add_argument("--variations", type=Path,
                        default=directory / "models" / "refined_variations.json")
    parser.add_argument("--selection-output", type=Path,
                        default=directory / "results" / "proposed_selection_test_results.csv")
    parser.add_argument("--retrieval-output", type=Path,
                        default=directory / "results" / "proposed_retrieval_test_results.csv")
    args = parser.parse_args()
    try:
        contract_status = run(args.contracts, args.output)
        selection_status = run_selection_example(
            args.variations, args.contracts, args.selection_output)
        retrieval_status = run_retrieval_examples(
            args.variations, args.contracts, args.retrieval_output)
        return max(contract_status, selection_status, retrieval_status)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Contract tests stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
