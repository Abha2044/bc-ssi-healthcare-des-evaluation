"""Split models/baseline_components.json into one file per component.

Run from the folder that contains validate_architecture.py and models/.

    python split_components.py --dry-run    # look only, write nothing
    python split_components.py              # do it

Writes:
    models/components/C*.json      one component each
    models/components/_order.json  the expected component list
    models/_conventions.json       the shared header

The original baseline_components.json is NOT deleted. After writing, the
script reloads what it wrote and compares it to the original. If the
round-trip is not identical it removes its own output and exits non-zero,
so a bad split cannot survive.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

SOURCE = Path("models") / "baseline_components.json"
COMPONENTS = Path("models") / "components"
CONVENTIONS = Path("models") / "_conventions.json"
ORDER = COMPONENTS / "_order.json"


def read_json(path):
    def unique(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError(f"{path}: duplicate JSON key {key}")
            seen[key] = value
        return seen
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would happen; write nothing")
    args = parser.parse_args()

    if not SOURCE.is_file():
        sys.exit(f"ERROR: {SOURCE} not found.\n"
                 f"       You are in: {Path.cwd()}\n"
                 f"       Run this from the folder that holds validate_architecture.py "
                 f"and models/.")

    model = read_json(SOURCE)
    if "components" not in model:
        sys.exit(f"ERROR: {SOURCE} has no 'components' key.")

    components = model["components"]
    header = {k: v for k, v in model.items() if k != "components"}
    ids = [c["id"] for c in components]

    if len(ids) != len(set(ids)):
        sys.exit("ERROR: duplicate component IDs in the source file.")
    bad = [i for i in ids if not i or "/" in i or "\\" in i or i.startswith("_")]
    if bad:
        sys.exit(f"ERROR: component IDs unusable as filenames: {bad}")

    print(f"Source      : {SOURCE}  ({SOURCE.stat().st_size:,} bytes)")
    print(f"Components  : {len(components)}")
    print(f"Header keys : {', '.join(header) or '(none)'}")
    print()
    verb = "would write" if args.dry_run else "writing   "
    for c in components:
        print("  " + verb + "  {:<42} {}".format(str(COMPONENTS / (c['id'] + '.json')), c.get('name', '')))
    print("  " + verb + "  " + str(ORDER))
    print("  " + verb + "  " + str(CONVENTIONS))
    print()

    if args.dry_run:
        print("Dry run: nothing was written.")
        print("Re-run without --dry-run to apply.")
        return 0

    if COMPONENTS.exists() and any(COMPONENTS.iterdir()):
        sys.exit(f"ERROR: {COMPONENTS} already exists and is not empty.\n"
                 f"       Move it aside first; this script will not overwrite it.")

    COMPONENTS.mkdir(parents=True, exist_ok=True)
    try:
        for c in components:
            write_json(COMPONENTS / f"{c['id']}.json", c)
        write_json(ORDER, {
            "note": "Load order for components/*.json. The loader fails if this "
                    "list and the folder contents disagree.",
            "components": ids,
        })
        write_json(CONVENTIONS, header)

        # Reload everything that was written and compare to the original.
        back = [read_json(COMPONENTS / f"{cid}.json") for cid in read_json(ORDER)["components"]]
        if back != components:
            raise ValueError("component round-trip differs from the source")
        if read_json(CONVENTIONS) != header:
            raise ValueError("header round-trip differs from the source")
    except Exception as error:
        shutil.rmtree(COMPONENTS, ignore_errors=True)
        CONVENTIONS.unlink(missing_ok=True)
        sys.exit(f"ERROR: {error}\n       Output removed; your repository is unchanged.")

    print(f"Wrote {len(components)} component files to {COMPONENTS}")
    print(f"Lossless check: PASSED  ({len(components)} components, header preserved)")
    print()
    print(f"{SOURCE} was NOT deleted. It is removed in step 2, after the loader works.")
    print()
    print("Next:")
    print("  git add models/components models/_conventions.json")
    print('  git commit -m "Split component inventory into one file per component"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
