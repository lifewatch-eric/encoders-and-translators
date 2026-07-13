#!/usr/bin/env python3
"""
transformations/ISO19139_to_EML220/run.py
=============================================
One-command runner for the ISO 19139 → EML 2.2.0 transformation.

What it does
────────────
1. Scans examples/input/ for every .xml file
2. Skips files that already have a matching output (unless --force)
3. Transforms only NEW files → writes result to examples/output/
4. Runs the full test suite against each new file
5. Prints the output path(s) marked NEW

Usage
─────
    python3 run.py                             # transform all new inputs
    python3 run.py --force                     # re-transform everything
    python3 run.py --input /path/to/file.xml   # single file
    python3 run.py --input file.xml --output result.xml
    python3 run.py --package-id my.new.id      # override packageId
    python3 run.py --system https://my-catalogue.eu  # override system
    python3 run.py --no-tests                  # transform only
    python3 run.py --open-folder               # open output/ in Finder/Files
    python3 run.py --quiet                     # errors + summary only

Requirements: pip install lxml
"""

import sys
import os
import argparse
import subprocess
import platform
from datetime import datetime, timezone
from pathlib import Path
from lxml import etree

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent.resolve()
XSL_PATH    = HERE / "xslt"    / "main.xsl"
INPUT_DIR   = HERE / "examples" / "input"
OUTPUT_DIR  = HERE / "examples" / "output"
TEST_SCRIPT = HERE / "test_transformation.py"

# ── Terminal colours ───────────────────────────────────────────────────────────
GREEN = "\033[32m"; RED = "\033[31m"; YELLOW = "\033[33m"
CYAN  = "\033[36m"; BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"

GMD_NS = "http://www.isotc211.org/2005/gmd"


# ── Helpers ────────────────────────────────────────────────────────────────────
def banner(text, char="━"):
    print(f"\n{BOLD}{char*64}{RESET}\n{BOLD}  {text}{RESET}\n{BOLD}{char*64}{RESET}")

def section(text):   print(f"\n{CYAN}{BOLD}▸ {text}{RESET}")
def ok(text):        print(f"  {GREEN}✅{RESET}  {text}")
def warn(text):      print(f"  {YELLOW}⚠ {RESET}  {text}")
def err(text):       print(f"  {RED}✗  {RESET}  {text}", file=sys.stderr)


def is_iso19139(path: Path) -> bool:
    try:
        root = etree.parse(str(path)).getroot()
        return root.tag == f"{{{GMD_NS}}}MD_Metadata"
    except Exception:
        return False


def open_folder(path: Path):
    try:
        system = platform.system()
        if system == "Darwin":   subprocess.run(["open",      str(path)], check=False)
        elif system == "Linux":  subprocess.run(["xdg-open",  str(path)], check=False)
        elif system == "Windows":subprocess.run(["explorer",  str(path)], check=False)
    except Exception:
        pass


def input_to_output_name(name: str) -> str:
    stem = Path(name).stem
    ext  = Path(name).suffix
    for old, new in [("iso19139", "eml220"), ("iso-19139", "eml220"),
                      ("iso_19139", "eml220"), ("ISO19139", "EML220")]:
        if old in stem:
            return stem.replace(old, new, 1) + ext
    return stem + "_eml220" + ext


# ── Core transform ─────────────────────────────────────────────────────────────
def transform_file(input_path, output_path, transform, params, quiet):
    if not quiet:
        print(f"\n  {DIM}Input  :{RESET} {input_path.name}")
        print(f"  {DIM}Output :{RESET} {output_path.name}")

    try:
        src_doc = etree.parse(str(input_path))
    except etree.XMLSyntaxError as e:
        err(f"XML parse error in {input_path.name}:\n       {e}")
        return False

    # Pre-flight: must be ISO 19139
    root_tag = src_doc.getroot().tag
    if root_tag != f"{{{GMD_NS}}}MD_Metadata":
        warn(f"{input_path.name} does not appear to be ISO 19139 (root: {root_tag!r})")
        warn("This stylesheet transforms FROM ISO 19139 (gmd:MD_Metadata).")
        return False

    try:
        result = transform(src_doc, **params)
    except etree.XSLTApplyError as e:
        err(f"Transformation failed for {input_path.name}:\n       {e}")
        return False

    if transform.error_log:
        for entry in transform.error_log:
            warn(f"XSLT warning: {entry}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_bytes = etree.tostring(
        result.getroot(), pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )
    with open(output_path, "wb") as fh:
        fh.write(output_bytes)

    size_kb = output_path.stat().st_size / 1024
    if not quiet:
        ok(f"Written → {output_path}  ({size_kb:.1f} KB)")
    return True


# ── Test runner ────────────────────────────────────────────────────────────────
def run_tests(input_path, quiet):
    if not TEST_SCRIPT.exists():
        warn("test_transformation.py not found — skipping tests.")
        return 0, 0

    cmd    = [sys.executable, str(TEST_SCRIPT), "--input", str(input_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(HERE))
    output = result.stdout + result.stderr

    if not quiet:
        for line in output.splitlines():
            print(f"    {line}")
    else:
        for line in output.splitlines():
            if "FAIL" in line or "ERROR" in line:
                print(f"    {line}")

    passed = failed = 0
    for line in output.splitlines():
        if "Passed:" in line and "Failed:" in line:
            try:
                parts = line.replace("│", "|").split("|")
                for p in parts:
                    p = p.strip()
                    if p.startswith("Passed:"): passed = int(p.split(":")[1].strip())
                    elif p.startswith("Failed:"): failed = int(p.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
    return passed, failed


# ── CLI ────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Auto-transform ISO 19139 → EML 2.2.0 and run tests.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--input",  "-i", type=Path, default=None, metavar="FILE",
        help="Single ISO 19139 file to transform (default: scan examples/input/)")
    p.add_argument("--output", type=Path, default=None, metavar="FILE",
        help="Save result to this specific path")
    p.add_argument("--force", "-f", action="store_true",
        help="Re-transform even if output already exists")
    p.add_argument("--package-id", default=None, metavar="ID",
        help="Override packageId in the output")
    p.add_argument("--system", default=None, metavar="URL",
        help="Override the eml:eml/@system attribute")
    p.add_argument("--no-tests", action="store_true",
        help="Skip test suite after transformation")
    p.add_argument("--open-folder", action="store_true",
        help="Open examples/output/ in file manager after run")
    p.add_argument("--quiet", "-q", action="store_true",
        help="Suppress verbose output; only show errors and summary")
    return p.parse_args()


def main():
    args = parse_args()

    banner("ISO 19139 → EML 2.2.0  ·  Transform & Test Runner")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"  {DIM}Started    : {ts}{RESET}")
    print(f"  {DIM}Stylesheet : {XSL_PATH}{RESET}")

    if not XSL_PATH.exists():
        err(f"Stylesheet not found: {XSL_PATH}"); sys.exit(1)

    try:
        xsl_doc   = etree.parse(str(XSL_PATH))
        transform = etree.XSLT(xsl_doc)
    except etree.XMLSyntaxError as e:
        err(f"Could not parse stylesheet:\n  {e}"); sys.exit(1)

    # Build XSLT parameter dict
    xslt_params = {}
    if args.package_id:
        xslt_params["package-id"] = etree.XSLT.strparam(args.package_id)
    if args.system:
        xslt_params["system"] = etree.XSLT.strparam(args.system)

    # Discover input files
    if args.input:
        input_files = [args.input.resolve()]
        if not input_files[0].exists():
            err(f"Input file not found: {input_files[0]}"); sys.exit(1)
    else:
        if not INPUT_DIR.exists():
            err(f"Input directory not found: {INPUT_DIR}"); sys.exit(1)
        input_files = sorted(INPUT_DIR.glob("*.xml"))
        if not input_files:
            err(f"No .xml files found in {INPUT_DIR}")
            print(f"\n  Drop your ISO 19139 file into:\n  {CYAN}{INPUT_DIR}{RESET}\n")
            sys.exit(1)

    section(f"Found {len(input_files)} input file(s)")
    for f in input_files:
        print(f"  {DIM}·{RESET} {f.name}")

    section("Running transformations")
    transformed: list[tuple] = []
    skipped:     list[Path]  = []
    failed_xform:list[Path]  = []

    for inp in input_files:
        if args.output and len(input_files) == 1:
            out_path = args.output.resolve()
        else:
            out_name = input_to_output_name(inp.name)
            out_path = OUTPUT_DIR / out_name

        if out_path.exists() and not args.force:
            if not args.quiet:
                warn(f"{inp.name} → output exists ({out_path.name}) — skipping.")
                warn("  Use --force to re-transform.")
            skipped.append(inp)
            continue

        success = transform_file(inp, out_path, transform, xslt_params, args.quiet)
        if success: transformed.append((inp, out_path))
        else:       failed_xform.append(inp)

    # Tests
    total_passed = total_failed = 0
    if not args.no_tests:
        inputs_to_test = [inp for inp, _ in transformed]
        if not inputs_to_test and skipped:
            section("No new transformations — running tests on existing outputs")
            inputs_to_test = [
                inp for inp in skipped
                if (OUTPUT_DIR / input_to_output_name(inp.name)).exists()
            ]
        if inputs_to_test:
            section(f"Running test suite ({len(inputs_to_test)} file(s))")
            for inp in inputs_to_test:
                if not args.quiet:
                    print(f"\n  {CYAN}Testing:{RESET} {inp.name}")
                p, f = run_tests(inp, args.quiet)
                total_passed += p; total_failed += f

    # Output listing
    all_outputs = sorted(OUTPUT_DIR.glob("*.xml")) if OUTPUT_DIR.exists() else []
    section("Output files  ←  ready to download")
    for out in all_outputs:
        size_kb = out.stat().st_size / 1024
        marker  = f"{GREEN}NEW{RESET} " if any(o == out for _, o in transformed) else "    "
        print(f"  {marker}{CYAN}{out}{RESET}  ({size_kb:.1f} KB)")
    print(f"\n  {DIM}Folder : {OUTPUT_DIR}{RESET}")

    # Summary
    banner("Summary", char="─")
    print(f"  Inputs processed  : {len(input_files)}")
    print(f"  Transformed       : {GREEN}{len(transformed)}{RESET}")
    print(f"  Skipped (exists)  : {DIM}{len(skipped)}{RESET}")
    print(f"  Failed            : {RED if failed_xform else DIM}{len(failed_xform)}{RESET}")
    if not args.no_tests and (total_passed + total_failed) > 0:
        print(f"  Tests passed      : {GREEN}{total_passed}{RESET}")
        print(f"  Tests failed      : {RED if total_failed else DIM}{total_failed}{RESET}")

    overall_ok = not failed_xform and total_failed == 0
    print()
    if overall_ok:
        print(f"  {GREEN}{BOLD}🎉  All done — transformation complete and tests pass.{RESET}")
    else:
        print(f"  {RED}{BOLD}⚠   Completed with errors — see details above.{RESET}")

    print(f"\n  {BOLD}To download your files:{RESET}")
    print(f"  Copy from:  {CYAN}{OUTPUT_DIR}{RESET}")
    print(f"  Or run:     {DIM}open {OUTPUT_DIR}  (macOS)  /  xdg-open {OUTPUT_DIR}  (Linux){RESET}\n")

    if args.open_folder and OUTPUT_DIR.exists():
        open_folder(OUTPUT_DIR)

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
