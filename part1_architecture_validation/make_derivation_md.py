"""Render evidence/r7_criterion_derivation.csv as a readable Markdown page.

Run from part1_architecture_validation/ AFTER moving the CSV into evidence/:

    mv results/r7_criterion_derivation.csv evidence/
    python make_derivation_md.py

Writes evidence/r7_criterion_derivation.md - the file the docs already cite.
The CSV stays as the machine-readable source; the Markdown is generated from it.
"""
import csv
import sys
from pathlib import Path

CSV = Path("evidence") / "r7_criterion_derivation.csv"
OUT = Path("evidence") / "r7_criterion_derivation.md"

NEEDED = ["check_id", "assessment_scope", "R7_requirement_element",
          "source_interaction", "derivation_rationale", "applicable_components",
          "evidence_threshold", "baseline_verdict"]

VERDICT = {"supported": "supported", "unsupported": "**unsupported**",
           "undetermined": "**unresolved**", "not_applicable": "n/a"}


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def main():
    if not CSV.is_file():
        sys.exit(f"ERROR: {CSV} not found.\n"
                 f"       You are in: {Path.cwd()}\n"
                 f"       Move it first:  mv results/r7_criterion_derivation.csv evidence/")

    with CSV.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        sys.exit(f"ERROR: {CSV} has no data rows.")
    missing = [c for c in NEEDED if c not in rows[0]]
    if missing:
        sys.exit(f"ERROR: {CSV} is missing columns: {missing}\n"
                 f"       Found: {list(rows[0])}")

    refined = next((c for c in rows[0] if "refined" in c.lower()), None)
    proposed = next((c for c in rows[0] if "proposed" in c.lower()), None)

    direct = [r for r in rows if r["assessment_scope"].strip().lower().startswith("direct")]
    other = [r for r in rows if r not in direct]

    def verdict(row, column):
        return VERDICT.get((row.get(column) or "").strip().lower(), cell(row.get(column, "")))

    out = [
        "# R7 criterion derivation",
        "",
        "Where each assessment criterion comes from, and what evidence it would take",
        "to settle it. Generated from `r7_criterion_derivation.csv` in this folder -",
        "edit the CSV, then re-run `make_derivation_md.py`.",
        "",
        "Each criterion is derived from one element of the R7 requirement and one",
        "documented interaction in the source appendices. The **evidence threshold**",
        "column states, in advance, what would count as settling it. Thresholds were",
        "fixed before the verdicts were recorded, so a verdict cannot be justified by",
        "whatever evidence happened to be available.",
        "",
        f"**{len(direct)} direct criteria** determine R7 coverage. "
        + (f"**{len(other)} supplementary criteri{'on is' if len(other) == 1 else 'a are'}** "
           "reported separately." if other else ""),
        "",
        "## Summary",
        "",
    ]

    headers = ["Criterion", "Scope", "R7 element", "Components", "Baseline"]
    if refined:
        headers.append("C4\\*+C6\\*")
    if proposed:
        headers.append("Proposed")
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        line = [f"`{cell(row['check_id'])}`", cell(row["assessment_scope"]),
                cell(row["R7_requirement_element"]), cell(row["applicable_components"]),
                verdict(row, "baseline_verdict")]
        if refined:
            line.append(verdict(row, refined))
        if proposed:
            line.append(verdict(row, proposed))
        out.append("| " + " | ".join(line) + " |")

    out += ["", "## Criterion by criterion", ""]
    for label, group in (("Direct criteria", direct), ("Supplementary criteria", other)):
        if not group:
            continue
        out += [f"### {label}", ""]
        for row in group:
            out += [
                f"#### `{cell(row['check_id'])}` — {cell(row['R7_requirement_element'])}",
                "",
                f"- **Components:** {cell(row['applicable_components'])}",
                f"- **Source interaction:** {cell(row['source_interaction'])}",
                f"- **Why this is a criterion:** {cell(row['derivation_rationale'])}",
                f"- **Evidence threshold:** {cell(row['evidence_threshold'])}",
                f"- **Baseline verdict:** {verdict(row, 'baseline_verdict')}",
            ]
            if refined:
                out.append(f"- **C4\\*+C6\\* verdict:** {verdict(row, refined)}")
            if proposed:
                out.append(f"- **Proposed design verdict:** {verdict(row, proposed)}")
            out.append("")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}  ({len(rows)} criteria: {len(direct)} direct, {len(other)} supplementary)")
    print()
    print("Next:")
    print("  git add evidence/r7_criterion_derivation.csv evidence/r7_criterion_derivation.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
