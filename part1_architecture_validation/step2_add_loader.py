"""Point validate_architecture.py at models/components/ instead of the single file.

Run from the folder that contains validate_architecture.py.

    python step2_add_loader.py --dry-run
    python step2_add_loader.py

Makes validate_architecture.py.bak before changing anything.
Safe to run twice: it detects an already-patched file and stops.
"""
import argparse
import shutil
import sys
from pathlib import Path

TARGET = Path("validate_architecture.py")
OLD = 'components = indexed(read_json(models / "baseline_components.json")["components"], "component")'
NEW = 'components = indexed(load_components(models), "component")'
IMPORT_AFTER = "from pathlib import Path\n"
IMPORT_LINE = "\nfrom modelio import load_components\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not TARGET.is_file():
        sys.exit(f"ERROR: {TARGET} not found.\n       You are in: {Path.cwd()}")
    if not Path("modelio.py").is_file():
        sys.exit("ERROR: modelio.py not found. Save it in this folder first.")
    if not Path("models/components/_order.json").is_file():
        sys.exit("ERROR: models/components/_order.json not found. Run split_components.py first.")

    text = TARGET.read_text(encoding="utf-8")

    if NEW in text:
        print("Already patched. Nothing to do.")
        return 0
    if OLD not in text:
        sys.exit("ERROR: could not find the line to replace:\n"
                 f"  {OLD}\n"
                 "       Your file differs from the version reviewed. Patch it by hand,\n"
                 "       or send me your validate_architecture.py.")
    if IMPORT_AFTER not in text:
        sys.exit("ERROR: no 'from pathlib import Path' line to anchor the import to.")

    patched = text.replace(OLD, NEW).replace(IMPORT_AFTER, IMPORT_AFTER + IMPORT_LINE, 1)

    print("In validate_architecture.py:")
    print("  - " + OLD)
    print("  + " + NEW)
    print("  + from modelio import load_components   (after the pathlib import)")
    print()

    if args.dry_run:
        print("Dry run: nothing was written.")
        return 0

    shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(patched, encoding="utf-8")
    print(f"Backup : {TARGET.with_suffix('.py.bak')}")
    print(f"Patched: {TARGET}")
    print()
    print("Next: python validate_architecture.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
