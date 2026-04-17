#!/usr/bin/env python3
"""
transformations/EML211_to_EML220/run.py
========================================
One-command runner for the EML 2.1.1 → EML 2.2.0 transformation.

What it does
────────────
1. Scans examples/input/ for every .xml file
2. For each input, checks whether a matching output already exists
3. If no output exists (or --force is given), runs the transformation
   and writes the result to examples/output/<same-filename>
4. Runs the full test suite against every transformed file
5. Prints a summary and the path(s) you can open / download

Usage
─────
    # Transform every new input file, then test:
    python3 run.py

    # Force re-transform even if output already exists:
    python3 run.py --force

    # Transform a single file:
    python3 run.py --input examples/input/my-dataset-eml211.xml

    # Override packageId for all outputs:
    python3 run.py --package-id my.new.package.id

    # Quiet mode — only show errors and the final summary:
    python3 run.py --quiet

Requirements
────────────
    pip install lxml          # only dependency

Download
────────
After the run, each output file path is printed. On macOS/Linux you
can also open the output folder in Finder / Files:
    open examples/output/          # macOS
    xdg-open examples/output/      # Linux
"""

import sys
import os
import argparse
import shutil
import subprocess
import platform
from datetime import datetime, timezone
from pathlib import Path
from lxml import etree
from typing import Optional


# ── Paths ──────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent.resolve()
XSL_PATH    = HERE / "xslt"    / "main.xsl"
INPUT_DIR   = HERE / "examples" / "input"
OUTPUT_DIR  = HERE / "examples" / "output"
TEST_SCRIPT = HERE / "test_transformation.py"

# ── Terminal colours ───────────────────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

EML211_URIS = ["eml://ecoinformatics.org/eml-2.1.1", "eml-2.1.1"]
EML220_NS   = "https://eml.ecoinformatics.org/eml-2.2.0"


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def banner(text: str, char: str = "━"):
    width = 64
    print(f"\n{BOLD}{char * width}{RESET}")
    print(f"{BOLD}  {text}{RESET}")
    print(f"{BOLD}{char * width}{RESET}")


def section(text: str):
    print(f"\n{CYAN}{BOLD}▸ {text}{RESET}")


def ok(text: str):
    print(f"  {GREEN}✅{RESET}  {text}")


def warn(text: str):
    print(f"  {YELLOW}⚠ {RESET}  {text}")


def err(text: str):
    print(f"  {RED}✗  {RESET}  {text}", file=sys.stderr)


def is_eml211(xml_path: Path) -> bool:
    """Return True if the file has an EML 2.1.1 namespace on the root."""
    try:
        root = etree.parse(str(xml_path)).getroot()
        ns = root.nsmap.get("eml", "")
        return any(uri in ns for uri in EML211_URIS)
    except Exception:
        return False


def is_eml220(xml_path: Path) -> bool:
    """Return True if the file already has an EML 2.2.0 namespace."""
    try:
        root = etree.parse(str(xml_path)).getroot()
        ns = root.nsmap.get("eml", "")
        return EML220_NS in ns
    except Exception:
        return False


def open_folder(path: Path):
    """Open a folder in the system file manager (best-effort)."""
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(path)], check=False)
        elif system == "Windows":
            subprocess.run(["explorer", str(path)], check=False)
    except Exception:
        pass  # silently ignore if no file manager available


def input_to_output_name(input_name: str) -> str:
    """
    Derive the output filename from the input filename.
    Replaces 'eml211' / '211' / 'input' with the EML 2.2.0 equivalent.
    Falls back to inserting '_eml220' before the extension.
    """
    stem = Path(input_name).stem
    ext  = Path(input_name).suffix

    replacements = [
        ("eml211",  "eml220"),
        ("eml_211", "eml_220"),
        ("EML211",  "EML220"),
        ("2.1.1",   "2.2.0"),
    ]
    for old, new in replacements:
        if old in stem:
            return stem.replace(old, new, 1) + ext

    return stem + "_eml220" + ext


# ══════════════════════════════════════════════════════════════════════════════
# Core transformation
# ══════════════════════════════════════════════════════════════════════════════

def transform_file(
    input_path: Path,
    output_path: Path,
    transform: etree.XSLT,
    package_id: Optional[str],
    schema_mode: str = "canonical",
    quiet: bool = False,
) -> bool:
    """
    Transform a single EML 2.1.1 file and write the result.
    Returns True on success, False on failure.
    """
    if not quiet:
        print(f"\n  {DIM}Input  :{RESET} {input_path.name}")
        print(f"  {DIM}Output :{RESET} {output_path.name}")

    # ── Parse ──────────────────────────────────────────────────────────────────
    try:
        src_doc = etree.parse(str(input_path))
    except etree.XMLSyntaxError as e:
        err(f"XML parse error in {input_path.name}:\n       {e}")
        err("Make sure the file is valid UTF-8 encoded XML.")
        return False

    # ── Version check ──────────────────────────────────────────────────────────
    root_ns = src_doc.getroot().nsmap.get("eml", "")
    if EML220_NS in root_ns:
        warn(f"{input_path.name} is already EML 2.2.0 — skipping transformation.")
        warn("This stylesheet upgrades FROM 2.1.1.  If you want to re-process,")
        warn("make sure you are supplying an EML 2.1.1 source file.")
        return False

    if not any(uri in root_ns for uri in EML211_URIS):
        warn(f"{input_path.name} does not appear to be EML 2.1.1 (namespace: {root_ns!r})")
        warn("Continuing anyway — check the output carefully.")

    # ── Apply XSLT ─────────────────────────────────────────────────────────────
    xslt_params: dict = {"schema-mode": etree.XSLT.strparam(schema_mode)}
    if package_id:
        xslt_params["package-id"] = etree.XSLT.strparam(package_id)

    try:
        result = transform(src_doc, **xslt_params)
    except etree.XSLTApplyError as e:
        err(f"Transformation failed for {input_path.name}:\n       {e}")
        return False

    if transform.error_log:
        for entry in transform.error_log:
            warn(f"XSLT warning: {entry}")

    # ── Write output ───────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Serialise and inject xmlns:stmml declaration on the root element.
    # libxslt strips unused namespace prefixes from the output tree;
    # stmml is referenced only in xsi:schemaLocation text (not in element
    # names), so it gets stripped. We reinsert it with a simple string replace
    # on the serialised XML — safe because the root tag is unique.
    output_bytes = etree.tostring(
        result.getroot(),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    output_str = output_bytes.decode("UTF-8")
    _old_root = '<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"'
    _new_root = (
        '<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"'
        ' xmlns:stmml="http://www.xml-cml.org/schema/stmml-1.2"'
    )
    if _old_root in output_str:
        output_str = output_str.replace(_old_root, _new_root, 1)
    output_bytes = output_str.encode("UTF-8")

    with open(output_path, "wb") as fh:
        fh.write(output_bytes)

    size_kb = output_path.stat().st_size / 1024
    if not quiet:
        ok(f"Written → {output_path}  ({size_kb:.1f} KB)")

    return True


# ══════════════════════════════════════════════════════════════════════════════
# Test runner
# ══════════════════════════════════════════════════════════════════════════════

def run_tests(input_path: Path, quiet: bool) -> tuple[int, int]:
    """
    Run test_transformation.py for a given input file.
    Returns (passed, failed) counts parsed from the summary line.
    """
    if not TEST_SCRIPT.exists():
        warn("test_transformation.py not found — skipping tests.")
        return 0, 0

    cmd = [sys.executable, str(TEST_SCRIPT), "--input", str(input_path)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(HERE),
    )

    output = result.stdout + result.stderr

    if not quiet:
        # Print the test output indented
        for line in output.splitlines():
            print(f"    {line}")
    else:
        # In quiet mode only print failures
        for line in output.splitlines():
            if "FAIL" in line or "ERROR" in line:
                print(f"    {line}")

    # Parse summary line e.g. "Total: 31  │  Passed: 31  │  Failed: 0"
    passed = failed = 0
    for line in output.splitlines():
        if "Passed:" in line and "Failed:" in line:
            try:
                parts = line.replace("│", "|").split("|")
                for p in parts:
                    p = p.strip()
                    if p.startswith("Passed:"):
                        passed = int(p.split(":")[1].strip())
                    elif p.startswith("Failed:"):
                        failed = int(p.split(":")[1].strip())
            except (ValueError, IndexError):
                pass

    return passed, failed


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Auto-transform EML 2.1.1 → EML 2.2.0 and run tests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--input", "-i",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Path to a single EML 2.1.1 XML file to transform. "
            "If omitted, all .xml files in examples/input/ are processed."
        ),
    )
    p.add_argument(
        "--force", "-f",
        action="store_true",
        help="Re-transform even if the output file already exists.",
    )
    p.add_argument(
        "--package-id",
        default=None,
        metavar="ID",
        help="Override the packageId attribute in every output document.",
    )
    p.add_argument(
        "--schema-mode",
        default="canonical",
        choices=["canonical", "gbif"],
        help=(
            "xsi:schemaLocation XSD mode. "
            "'canonical' (default): uses ecoinformatics.org + cml.org schemas. "
            "'gbif': uses GBIF-hosted profile schemas (for IPT/GBIF submissions)."
        ),
    )
    p.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip the test suite (just transform, do not validate).",
    )
    p.add_argument(
        "--open-folder",
        action="store_true",
        help="Open examples/output/ in the system file manager after the run.",
    )
    p.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output; only show errors and the final summary.",
    )
    return p.parse_args()


def main():
    args = parse_args()

    # ── Title banner ───────────────────────────────────────────────────────────
    banner("EML 2.1.1 → EML 2.2.0  ·  Transform & Test Runner")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"  {DIM}Started : {ts}{RESET}")
    print(f"  {DIM}Stylesheet : {XSL_PATH}{RESET}")

    # ── Verify stylesheet ──────────────────────────────────────────────────────
    if not XSL_PATH.exists():
        err(f"Stylesheet not found: {XSL_PATH}")
        sys.exit(1)

    try:
        xsl_doc   = etree.parse(str(XSL_PATH))
        transform = etree.XSLT(xsl_doc)
    except etree.XMLSyntaxError as e:
        err(f"Could not parse stylesheet:\n  {e}")
        sys.exit(1)

    # ── Discover input files ───────────────────────────────────────────────────
    if args.input:
        input_files = [args.input.resolve()]
        if not input_files[0].exists():
            err(f"Input file not found: {input_files[0]}")
            sys.exit(1)
    else:
        if not INPUT_DIR.exists():
            err(f"Input directory not found: {INPUT_DIR}")
            sys.exit(1)
        input_files = sorted(INPUT_DIR.glob("*.xml"))
        if not input_files:
            err(f"No .xml files found in {INPUT_DIR}")
            print(f"\n  Drop your EML 2.1.1 file into:")
            print(f"  {CYAN}{INPUT_DIR}{RESET}")
            print(f"  then run this script again.\n")
            sys.exit(1)

    section(f"Found {len(input_files)} input file(s)")
    for f in input_files:
        print(f"  {DIM}·{RESET} {f.name}")

    # ── Transform loop ─────────────────────────────────────────────────────────
    section("Running transformations")

    transformed: list[tuple[Path, Path]] = []   # (input, output) pairs
    skipped:     list[Path]              = []
    failed_xform: list[Path]             = []

    for inp in input_files:
        out_name   = input_to_output_name(inp.name)
        output_path = OUTPUT_DIR / out_name

        if output_path.exists() and not args.force:
            if not args.quiet:
                warn(f"{inp.name} → output already exists ({out_name}) — skipping.")
                warn(f"  Use --force to re-transform.")
            skipped.append(inp)
            continue

        success = transform_file(
            input_path=inp,
            output_path=output_path,
            transform=transform,
            package_id=args.package_id,
            schema_mode=args.schema_mode,
            quiet=args.quiet,
        )

        if success:
            transformed.append((inp, output_path))
        else:
            failed_xform.append(inp)

    # ── Test loop ──────────────────────────────────────────────────────────────
    total_passed = total_failed = 0

    if not args.no_tests:
        all_inputs_to_test = [inp for inp, _ in transformed]

        if not all_inputs_to_test:
            if skipped:
                section("No new transformations — running tests on existing outputs")
                all_inputs_to_test = [
                    inp for inp in skipped
                    if (OUTPUT_DIR / input_to_output_name(inp.name)).exists()
                ]
            else:
                section("Nothing to test")

        if all_inputs_to_test:
            section(f"Running test suite ({len(all_inputs_to_test)} file(s))")
            for inp in all_inputs_to_test:
                if not args.quiet:
                    print(f"\n  {CYAN}Testing:{RESET} {inp.name}")
                p, f = run_tests(inp, quiet=args.quiet)
                total_passed += p
                total_failed += f

    # ── Output file list ───────────────────────────────────────────────────────
    all_outputs = sorted(OUTPUT_DIR.glob("*.xml")) if OUTPUT_DIR.exists() else []

    section("Output files  ←  ready to download")
    if all_outputs:
        for out in all_outputs:
            size_kb = out.stat().st_size / 1024
            marker  = f"{GREEN}NEW{RESET} " if any(o == out for _, o in transformed) else "    "
            print(f"  {marker}{CYAN}{out}{RESET}  ({size_kb:.1f} KB)")
    else:
        warn("No output files found.")

    print(f"\n  {DIM}Folder : {OUTPUT_DIR}{RESET}")

    # ── Final summary ──────────────────────────────────────────────────────────
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
    print(f"  Or run:     {DIM}open {OUTPUT_DIR}  (macOS)  /  "
          f"xdg-open {OUTPUT_DIR}  (Linux){RESET}\n")

    # ── Open folder if requested ───────────────────────────────────────────────
    if args.open_folder and OUTPUT_DIR.exists():
        open_folder(OUTPUT_DIR)
        print(f"  {DIM}Opened output folder in file manager.{RESET}\n")

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
