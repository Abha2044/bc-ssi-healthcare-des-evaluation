"""Create the main R7 baseline-vs-refined component/requirement comparison.

Use existing outputs only. This script does NOT rerun experiments, change
assessment verdicts, or assume ATAM-reported gaps are proven implementation failures.
Run from any directory:
    python part1_architecture_validation/build_r7_main_comparison.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
CONFIGS = ("baseline", "C4_star_only", "C6_star_only", "C4_C6_star")
PROPOSED = "R7_proposed_logical_design"


def read_csv(name):
    with (RESULTS / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    with (RESULTS / name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def md(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(md(h) for h in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(md(v) for v in row) + " |" for row in rows],
    ])


def main():
    crit = {(r["configuration"], r["check"]): r
            for r in read_csv("reference_criterion_assessment.csv")}
    cov = {r["configuration"]: r for r in read_csv("reference_requirement_coverage.csv")}
    perf = {(r["profile"], r["configuration"]): r
            for r in read_csv("r7_variation_experiment_summary.csv")}

    proposed_cases = {}
    for name in ("proposed_contract_test_results.csv",
                 "proposed_selection_test_results.csv",
                 "proposed_retrieval_test_results.csv"):
        for case in read_csv(name):
            proposed_cases[case["test"]] = case["result"]

    for config in (*CONFIGS, PROPOSED):
        if config not in cov:
            raise ValueError(f"Missing requirement coverage for {config}")
    for profile in ("shared_responsibilities", "atam_informed_availability"):
        for config in CONFIGS:
            if (profile, config) not in perf:
                raise ValueError(f"Missing experiment {profile}/{config}")

    limited = "atam_informed_availability"
    shared = "shared_responsibilities"
    baseline = perf[(limited, "baseline")]
    combined = perf[(limited, "C4_C6_star")]

    def ratio(c, numerator, denominator, profile=limited):
        r = perf[(profile, c)]
        return f"{r[numerator]}/{r[denominator]}"

    # Source labels are explicit human-reviewed mappings; judgments/results are read from CSV.
    # A supported *behaviour responsibility* does not necessarily prove interface compatibility.
    questions = [
        dict(q="Can C4 prepare the required obligations?", check="C4-OBLIGATIONS",
             components="C4", gap="G2 (ATAM)",
             change="C4* adds named C4.4 Obligation Handler (Appendix A, A-11).",
             model_cases="R7-T6", 
             effect="Policy selection outcomes in limited profile: baseline "
                    + ratio("baseline", "correct_selection_cases", "selection_cases")
                    + "; combined " + ratio("C4_C6_star", "correct_selection_cases", "selection_cases")
                    + ". Baseline selection was blocked by the assumed unavailability, not shown incorrect.",
             missing="Demonstrate correct obligation selection and C4* provider behaviour independently."),
        dict(q="Can C6 enforce the required restrictions?", check="C6-OBLIGATIONS-MECHANISM",
             components="C6", gap="G3 (ATAM)",
             change="C6* operationalizes already-specified C6.6 minimization (Appendix A, A-11).",
             model_cases="R7-T2,R7-T3,R7-T5",
             effect="Complete permitted deliveries in limited profile: baseline "
                    + ratio("baseline", "complete_permitted_delivery_cases", "permit_cases")
                    + "; combined " + ratio("C4_C6_star", "complete_permitted_delivery_cases", "permit_cases")
                    + ". This measures the whole modeled path, not isolated C6*.",
             missing="Show C6* implements mandatory masking/filtering for selected requests."),
        dict(q="Do C4 and C6 agree on obligation meaning?", check="I2-RESPONSE",
             components="C4 + C6", gap="G2/G3 related",
             change="C4.4 prepares obligations; C6.6 enforces them; common semantics are still needed.",
             model_cases="R7-T4,R7-T5,R7-T6",
             effect="Proposed I2 decision/obligation rules are exercised, not a separately executed baseline/variant interface.",
             missing="Specify and review shared payload, semantics, and failure handling for C4* to C6*."),
        dict(q="Does C15 provide authorized scoped records?", check="C15-SCOPE",
             components="C15", gap="No direct C15 variation in this R7 pilot",
             change="C15 is unchanged in the C4*/C6* variation comparison.",
             model_cases="R7-T7,R7-T8,R7-T9,R7-T10",
             effect="Proposed flat-record retrieval is tested using a supplied authorized scope.",
             missing="Confirm actual C15 retrieval enforcement and source of authorized scope."),
        dict(q="Do C6 and C15 preserve the same scope?", check="I3-SCOPE",
             components="C6 + C15", gap="G3 related; no direct I3 closure",
             change="The refinement must define the C6*/C15 responsibility split and scope contract.",
             model_cases="R7-T7,R7-T9,R7-T10",
             effect="Proposed scoped retrieval tests run, but there are no independently executed variant interfaces.",
             missing="Specify authorized scope provenance and provider/consumer compatibility."),
        dict(q="Are restrictions preserved to final release?", check="I4-DATA",
             components="C6 + C15", gap="G3 related",
             change="C6.6 availability alone does not prove end-to-end release invariants.",
             model_cases="R7-T5,R7-T7,R7-T9",
             effect="The proposed logical model enforces restrictions or blocks release in selected cases.",
             missing="Review/test the complete refined release path, including failures and combined restrictions."),
    ]

    rows = []
    for q in questions:
        check = q["check"]
        for config in (*CONFIGS, PROPOSED):
            if (config, check) not in crit:
                raise ValueError(f"Missing criterion result for {config}/{check}")
        b = crit[("baseline", check)]
        r = crit[("C4_C6_star", check)]
        test_results = "; ".join(
            f"{c.strip()}: {proposed_cases.get(c.strip(), 'NOT FOUND')}"
            for c in q["model_cases"].split(",")
        )
        rows.append({
            "requirement": "R7",
            "validation_question": q["q"],
            "criterion_id": check,
            "components": q["components"],
            "baseline_documentary_finding": b["rationale"],
            "baseline_verdict": b["verdict"],
            "atam_gap": q["gap"],
            "refined_component_change": q["change"],
            "combined_refined_documentary_finding": r["rationale"],
            "combined_refined_verdict": r["verdict"],
            "proposed_logical_design_verdict": crit[(PROPOSED, check)]["verdict"],
            "executable_comparison_or_scope": q["effect"],
            "linked_proposed_model_tests": test_results,
            "further_evidence_needed": q["missing"],
            "baseline_source": b["review_evidence_refs"],
        })
    write_csv("r7_main_component_requirement_comparison.csv", rows)

    main_rows = [
        (r["validation_question"],
         f"{r['baseline_verdict']}: {r['baseline_documentary_finding']}",
         f"{r['atam_gap']}; {r['refined_component_change']}",
         f"{r['combined_refined_verdict']}: {r['combined_refined_documentary_finding']}",
         r["executable_comparison_or_scope"],
         r["further_evidence_needed"])
        for r in rows
    ]
    overall = (
        "Does the complete architecture satisfy R7?",
        f"{cov['baseline']['coverage']} ({cov['baseline']['supported_checks']} supported, "
        f"{cov['baseline']['unresolved_checks']} unresolved, "
        f"{cov['baseline']['not_applicable_checks']} N/A)",
        "Combined C4.4 preparation and C6.6 enforcement availability (G2/G3).",
        f"{cov['C4_C6_star']['coverage']} ({cov['C4_C6_star']['supported_checks']} supported, "
        f"{cov['C4_C6_star']['unresolved_checks']} unresolved, "
        f"{cov['C4_C6_star']['not_applicable_checks']} N/A)",
        "Limited-assumption acceptance: baseline " + ratio("baseline", "accepted_cases", "cases")
        + "; combined " + ratio("C4_C6_star", "accepted_cases", "cases")
        + ". With shared availability: both "
        + ratio("baseline", "accepted_cases", "cases", shared) + ".",
        "Resolve I2/I3/I4 with evidence attributable to the defined combined refinement; do not transfer proposed-model verdicts.",
    )
    main_rows.append(overall)

    lines = [
        "# R7 — Requirement-to-component baseline/refinement comparison",
        "",
        "> Generated from existing Part 1 results. No new tests were performed and no coverage verdicts were changed.",
        "> ATAM findings motivate assumptions; the executable variants share model helpers and are not independent component implementations.",
        "",
        "## Main research result: Does the refinement improve R7 coverage?",
        "",
        table(("Validation question", "Baseline evidence", "ATAM gap / refined change",
               "Combined refinement evidence", "Executable evidence", "Still needed"), main_rows),
        "",
        "**Interpretation:** C4*+C6* yields better authorized delivery under the ATAM-informed limited-availability assumptions, "
        "but the available documentary criteria do not establish a higher R7 coverage verdict for the refinement-only configurations.",
        "",
        "## Architectural coverage by configuration (1.1 and 1.2)",
        "",
        table(("Configuration", "Supported", "Unresolved", "N/A", "Overall R7 coverage"), [
            (c, cov[c]["supported_checks"], cov[c]["unresolved_checks"],
             cov[c]["not_applicable_checks"], cov[c]["coverage"])
            for c in (*CONFIGS, PROPOSED)
        ]),
        "",
        "The proposed logical design includes additional contract assumptions. Its `full` verdict is bounded to its selected criteria; "
        "it is not a measured coverage improvement of the C4*/C6* refinements alone.",
        "",
        "## Executable comparison by assumption profile (1.2)",
        "",
    ]
    for profile in (shared, limited):
        lines.extend([
            "### " + profile,
            "",
            table(("Configuration", "Accepted", "Complete permitted delivery", "Correct C4 selection", "Privacy protected"), [
                (config,
                 ratio(config, "accepted_cases", "cases", profile),
                 ratio(config, "complete_permitted_delivery_cases", "permit_cases", profile),
                 ratio(config, "correct_selection_cases", "selection_cases", profile),
                 ratio(config, "privacy_protected_cases", "cases", profile))
                for config in CONFIGS
            ]),
            "",
        ])
    lines.extend([
        "**Caution:** When preparation is unavailable, selection is blocked rather than independently evaluated. "
        "Privacy protection includes blocking a request and does not imply successful delivery.",
        "",
        "## Traceable proposed-model tests (not baseline evidence)",
        "",
        table(("Question", "Criterion", "Baseline verdict", "Combined verdict", "Proposed verdict", "Existing proposed tests"), [
            (r["validation_question"], r["criterion_id"], r["baseline_verdict"],
             r["combined_refined_verdict"], r["proposed_logical_design_verdict"],
             r["linked_proposed_model_tests"])
            for r in rows
        ]),
        "",
        "## What this demonstrates",
        "",
        "- **1.1:** Documents the assigned R7 behaviours and identifies unresolved I2 (obligations), "
        "I3 (scope), and I4 (final release) interface evidence.",
        "- **1.2:** The modeled combined refinement improves expected authorized delivery under the ATAM-informed "
        "availability assumptions; no improvement appears when all mechanisms are assumed available.",
        "- **Not proven:** Historical baseline inability, independent C4*/C6* implementation compatibility, "
        "or full real-world R7 satisfaction. Supporting audit checks are assessed separately.",
        "",
        "## How to support a stronger refined-coverage claim",
        "",
        "1. Specify and independently review a C4* -> C6* decision-and-obligation interface (I2).",
        "2. Specify/review the C6* -> C15 authorization-scope contract (I3).",
        "3. Specify/review the final-release invariant (I4), and execute targeted tests against "
        "the declared *refined* interfaces rather than only a shared proposed helper.",
        "4. Reassess documentary coverage using attributable evidence; do not auto-promote verdicts from test counts.",
        "",
        "Sources: Appendix A, Tables A-0/A-3/A-11/A-13; Requirements Appendix B, R7 flow and Table C; "
        "`reference_criterion_assessment.csv`, `reference_requirement_coverage.csv`, "
        "`r7_variation_experiment_summary.csv`, and proposed test result CSVs.",
        "",
    ])
    out = RESULTS / "r7_main_component_requirement_comparison.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Wrote {RESULTS / 'r7_main_component_requirement_comparison.csv'}")


if __name__ == "__main__":
    main()
