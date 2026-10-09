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
    args = parser.parse_args()
    try:
        return run(args.contracts, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Contract tests stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
