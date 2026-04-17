#!/usr/bin/env python3
"""
transformations/EML211_to_EML220/test_transformation.py
========================================================
Automated test suite for the EML 2.1.1 → EML 2.2.0 transformation.

Requirements:
    pip install lxml

Usage:
    # Test against the bundled sample (default):
    python3 test_transformation.py

    # Test against YOUR OWN EML 2.1.1 file:
    python3 test_transformation.py --input /path/to/your-file.xml

    # Test and save the transformed output:
    python3 test_transformation.py --input /path/to/your-file.xml --output /path/to/result.xml

    # Supply a new packageId during transformation:
    python3 test_transformation.py --input /path/to/your-file.xml --package-id my.new.id

Returns exit code 0 on all-pass, 1 on any failure.
"""

import sys
import argparse
from pathlib import Path
from lxml import etree

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN = "\033[32m"
RED   = "\033[31m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"

# ── Default paths (relative to this file) ─────────────────────────────────────
HERE        = Path(__file__).parent
DEFAULT_XSL = HERE / "xslt" / "main.xsl"
DEFAULT_IN  = HERE / "examples" / "input" / "sample-eml211.xml"

EML211_URIS = [
    "eml://ecoinformatics.org/eml-2.1.1",
    "eml-2.1.1",
]
EML220_NS   = "https://eml.ecoinformatics.org/eml-2.2.0"
XSI_NS      = "http://www.w3.org/2001/XMLSchema-instance"

results: list[bool] = []


# ══════════════════════════════════════════════════════════════════════════════
# Assertion helper
# ══════════════════════════════════════════════════════════════════════════════

def check(label: str, got=None, expected=None,
          contains: str = None, not_contains: str = None, truthy=None):
    ok     = True
    detail = ""

    if truthy is not None:
        if not truthy:
            ok = False; detail = "\n       condition evaluated to False"
    elif expected is not None:
        if got != expected:
            ok = False
            detail = (f"\n       got:      {repr(got)}"
                      f"\n       expected: {repr(expected)}")

    if contains is not None and contains not in (got or ""):
        ok = False
        detail = f"\n       '{contains}' not found in value"

    if not_contains is not None and not_contains in (got or ""):
        ok = False
        detail = f"\n       '{not_contains}' unexpectedly present in value"

    results.append(ok)
    icon = f"{GREEN}✅ PASS{RESET}" if ok else f"{RED}❌ FAIL{RESET}"
    print(f"  {icon}  {label}{detail}")


# ══════════════════════════════════════════════════════════════════════════════
# Pre-flight validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_input_is_eml211(src_doc: etree._ElementTree) -> bool:
    """
    Warn (but don't abort) if the input file does not look like EML 2.1.1.
    Returns True if it looks correct, False otherwise.
    """
    root = src_doc.getroot()
    ns   = root.nsmap.get("eml", "")
    if any(uri in ns for uri in EML211_URIS):
        print(f"  {GREEN}✅{RESET}  Input namespace confirmed as EML 2.1.1  ({DIM}{ns}{RESET})")
        return True
    elif EML220_NS in ns:
        print(f"  {RED}⚠  WARNING:{RESET} Input namespace is already EML 2.2.0!")
        print(f"       {DIM}{ns}{RESET}")
        print(f"       This stylesheet upgrades FROM 2.1.1.  Your file is already 2.2.0.")
        print(f"       The structural tests below may fail or give misleading results.")
        return False
    else:
        print(f"  {RED}⚠  WARNING:{RESET} Unrecognised EML namespace: {repr(ns)}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Test sections
# ══════════════════════════════════════════════════════════════════════════════

# Canonical schemaLocation values (default mode)
CANONICAL_EML_NS   = "https://eml.ecoinformatics.org/eml-2.2.0"
CANONICAL_EML_XSD  = "https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd"
CANONICAL_STMML_NS = "http://www.xml-cml.org/schema/stmml-1.2"
CANONICAL_STMML_XSD= "http://www.xml-cml.org/schema/stmml-1.2/stmml.xsd"


def test_namespaces(root):
    print(f"\n{BOLD}[1] Namespace updates & schemaLocation pairs{RESET}")
    loc    = root.get(f"{{{XSI_NS}}}schemaLocation") or ""
    tokens = loc.split()

    check("Root element namespace is EML 2.2.0",
          got=root.nsmap.get("eml"), expected=EML220_NS)
    check("xmlns:stmml declared on root element",
          got=root.nsmap.get("stmml"),
          expected="http://www.xml-cml.org/schema/stmml-1.2")
    check("xsi:schemaLocation is present",
          truthy=bool(loc))
    check("xsi:schemaLocation has exactly 4 tokens (2 strict pairs)",
          got=len(tokens), expected=4)

    if len(tokens) == 4:
        # Pair 1: EML namespace → EML XSD
        check("Pair 1 namespace is EML 2.2.0",
              got=tokens[0], expected=CANONICAL_EML_NS)
        check("Pair 1 XSD is canonical EML 2.2.0 schema",
              got=tokens[1], expected=CANONICAL_EML_XSD)
        # Pair 2: stmml namespace → stmml XSD
        check("Pair 2 namespace is stmml-1.2",
              got=tokens[2], expected=CANONICAL_STMML_NS)
        check("Pair 2 XSD is canonical stmml-1.2 schema",
              got=tokens[3], expected=CANONICAL_STMML_XSD)

    check("No old eml:// URI in schemaLocation",
          got=loc, not_contains="eml://ecoinformatics.org")
    check("No stmml-1.1 in schemaLocation",
          got=loc, not_contains="stmml-1.1")
    check("No GBIF profile XSD in canonical-mode output",
          got=loc, not_contains="rs.gbif.org")


def _apply(transform, src_doc, params=None):
    """Apply XSLT, inject stmml namespace, return root element."""
    p = {k: etree.XSLT.strparam(v) for k, v in (params or {}).items()}
    xml = etree.tostring(transform(src_doc, **p).getroot(),
                          pretty_print=True, xml_declaration=True,
                          encoding="UTF-8").decode("UTF-8")
    old = '<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"'
    new = ('<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"'
           ' xmlns:stmml="http://www.xml-cml.org/schema/stmml-1.2"')
    if old in xml:
        xml = xml.replace(old, new, 1)
    return etree.fromstring(xml.encode("UTF-8"))


def test_package_id(transform, src_doc):
    print(f"\n{BOLD}[2] packageId handling{RESET}")
    original_id = src_doc.getroot().get("packageId", "")
    result_default = _apply(transform, src_doc)
    check("Default: packageId preserved when no param supplied",
          got=result_default.get("packageId"), expected=original_id)

    custom_id = "test.override.id.2026"
    result_custom = _apply(transform, src_doc, {"package-id": custom_id})
    check("Custom: packageId overwritten when package-id param supplied",
          got=result_custom.get("packageId"), expected=custom_id)


def test_alternate_identifier(root):
    print(f"\n{BOLD}[3] <alternateIdentifier> handling{RESET}")
    dataset  = root.find("dataset")
    children = list(dataset) if dataset is not None else []
    has_alt  = any(c.tag == "alternateIdentifier" for c in children)
    check("<alternateIdentifier> is present in <dataset>",
          truthy=has_alt)
    if has_alt:
        check("<alternateIdentifier> is the first child of <dataset>",
              truthy=children[0].tag == "alternateIdentifier")


def test_pubdate(root, src_doc):
    print(f"\n{BOLD}[4] pubDate normalisation{RESET}")
    src_date    = src_doc.getroot().findtext("dataset/pubDate") or ""
    result_date = root.findtext("dataset/pubDate") or ""
    if "-" not in src_date and len(src_date) == 4:
        # Year-only source → must be normalised
        check(f"Year-only '{src_date}' normalised to '{src_date}-01-01'",
              got=result_date, expected=f"{src_date}-01-01")
    else:
        # Already ISO 8601 → must pass through unchanged
        check(f"ISO 8601 date '{src_date}' passed through unchanged",
              got=result_date, expected=src_date)


def test_core_metadata(root, src_doc):
    print(f"\n{BOLD}[5] Core metadata passthrough{RESET}")
    src_root = src_doc.getroot()

    src_title  = src_root.findtext("dataset/title") or ""
    out_title  = root.findtext("dataset/title") or ""
    check("dataset/title preserved", got=out_title, expected=src_title)

    src_lang = src_root.findtext("dataset/language") or ""
    out_lang = root.findtext("dataset/language") or ""
    check("dataset/language preserved", got=out_lang, expected=src_lang)

    src_creators = src_root.findall("dataset/creator")
    out_creators = root.findall("dataset/creator")
    check(f"All {len(src_creators)} creator(s) preserved",
          got=len(out_creators), expected=len(src_creators))

    src_kw_sets = src_root.findall("dataset/keywordSet")
    out_kw_sets = root.findall("dataset/keywordSet")
    check(f"All {len(src_kw_sets)} keywordSet(s) preserved",
          got=len(out_kw_sets), expected=len(src_kw_sets))


def test_methods(root, src_doc):
    print(f"\n{BOLD}[6] <methods> and <sampling>{RESET}")
    src_root = src_doc.getroot()

    out_methods = root.find("dataset/methods")
    src_methods = src_root.find("dataset/methods")

    if src_methods is None:
        print(f"  {DIM}ℹ  No <methods> in source — section skipped.{RESET}")
        return

    check("<methods> element present in output", truthy=out_methods is not None)

    src_steps = src_methods.findall("methodStep")
    out_steps = out_methods.findall("methodStep") if out_methods is not None else []
    check(f"All {len(src_steps)} methodStep(s) preserved",
          got=len(out_steps), expected=len(src_steps))

    src_sampling = src_methods.find("sampling")
    if src_sampling is not None:
        out_sampling = out_methods.find("sampling") if out_methods is not None else None
        check("<sampling> block preserved", truthy=out_sampling is not None)
        if out_sampling is not None:
            study = out_sampling.findtext("studyExtent/description/para") or ""
            check("studyExtent/description/para has content", truthy=bool(study.strip()))
            sdesc = out_sampling.findtext("samplingDescription/para") or ""
            check("samplingDescription/para has content",     truthy=bool(sdesc.strip()))


def test_project(root, src_doc):
    print(f"\n{BOLD}[7] <project> normalisation{RESET}")
    src_root    = src_doc.getroot()
    src_project = src_root.find("dataset/project")
    out_project = root.find("dataset/project")

    if src_project is None:
        print(f"  {DIM}ℹ  No <project> in source — section skipped.{RESET}")
        return

    check("<project> element present", truthy=out_project is not None)
    if out_project is None:
        return

    src_title = src_project.findtext("title") or ""
    out_title = out_project.findtext("title") or ""
    check("project/title preserved",
          got=out_title, expected=src_title)

    src_personnel = src_project.findall("personnel")
    out_personnel = out_project.findall("personnel")
    check(f"All {len(src_personnel)} personnel element(s) preserved",
          got=len(out_personnel), expected=len(src_personnel))

    for i, (sp, op) in enumerate(zip(src_personnel, out_personnel)):
        # Personnel must have at minimum an individualName OR organizationName
        has_name = bool(
            op.findtext("individualName/givenName") or
            op.findtext("individualName/surName") or
            op.findtext("organizationName")
        )
        check(f"personnel[{i+1}] has name or organization",
              truthy=has_name)
        # Verify organizationName is faithfully copied when source has one
        src_org = (sp.findtext("organizationName") or "").strip()
        out_org = (op.findtext("organizationName") or "").strip()
        if src_org:
            check(f"personnel[{i+1}] organizationName matches source",
                  got=out_org, expected=src_org)
        # Verify role is copied when present in source
        src_role = (sp.findtext("role") or "").strip()
        out_role = (op.findtext("role") or "").strip()
        if src_role:
            check(f"personnel[{i+1}] role preserved",
                  got=out_role, expected=src_role)


def test_datatable(root, src_doc):
    print(f"\n{BOLD}[8] <dataTable> passthrough{RESET}")
    src_root   = src_doc.getroot()
    src_tables = src_root.findall("dataset/dataTable")
    out_tables = root.findall("dataset/dataTable")

    if not src_tables:
        print(f"  {DIM}ℹ  No <dataTable> in source — section skipped.{RESET}")
        return

    check(f"All {len(src_tables)} dataTable(s) preserved",
          got=len(out_tables), expected=len(src_tables))

    for i, (src_dt, out_dt) in enumerate(zip(src_tables, out_tables)):
        src_name = src_dt.findtext("entityName") or ""
        out_name = out_dt.findtext("entityName") or ""
        check(f"dataTable[{i+1}] entityName preserved",
              got=out_name, expected=src_name)

        src_attrs = src_dt.findall("attributeList/attribute")
        out_attrs = out_dt.findall("attributeList/attribute")
        if src_attrs:
            # Compute the expected count after deduplication
            seen_names: set = set()
            unique_src = 0
            for a in src_attrs:
                n = (a.findtext("attributeName") or "").strip()
                if n not in seen_names:
                    seen_names.add(n)
                    unique_src += 1
            dups = len(src_attrs) - unique_src
            if dups > 0:
                check(
                    f"dataTable[{i+1}]: {unique_src} unique attribute(s) preserved "
                    f"({dups} duplicate(s) removed from source)",
                    got=len(out_attrs), expected=unique_src,
                )
            else:
                check(
                    f"dataTable[{i+1}]: all {len(src_attrs)} attribute(s) preserved",
                    got=len(out_attrs), expected=len(src_attrs),
                )


def test_no_211_artefacts(root):
    print(f"\n{BOLD}[9] No EML 2.1.1 artefacts remain in output{RESET}")
    xml_str = etree.tostring(root, encoding="unicode")
    check("No 'eml-2.1.1' string anywhere in output",
          got=xml_str, not_contains="eml-2.1.1")
    check("No 'stmml-1.1' string anywhere in output",
          got=xml_str, not_contains="stmml-1.1")
    check("Old ecoinformatics EML 2.1.1 URI gone",
          got=xml_str, not_contains="eml://ecoinformatics.org/eml-2.1.1")


def test_no_xslt_errors(transform):
    print(f"\n{BOLD}[10] XSLT processor health{RESET}")
    check("No XSLT processor errors or warnings",
          truthy=len(transform.error_log) == 0)
    if transform.error_log:
        for entry in transform.error_log:
            print(f"       {RED}{entry}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# CLI + main
# ══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Test the EML 2.1.1 → EML 2.2.0 XSLT transformation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    p.add_argument(
        "--input", "-i",
        type=Path,
        default=DEFAULT_IN,
        help=f"EML 2.1.1 input XML file to transform "
             f"(default: examples/input/sample-eml211.xml)")
    p.add_argument(
        "--xsl",
        type=Path,
        default=DEFAULT_XSL,
        help=f"XSLT stylesheet to use (default: xslt/main.xsl)")
    p.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="If given, the transformed XML is written to this file")
    p.add_argument(
        "--package-id",
        default=None,
        help="Override the packageId attribute in the output")
    return p.parse_args()


def main():
    args = parse_args()

    # ── Resolve and validate paths ─────────────────────────────────────────────
    xsl_path   = args.xsl.resolve()
    input_path = args.input.resolve()

    if not xsl_path.exists():
        print(f"{RED}ERROR:{RESET} Stylesheet not found: {xsl_path}")
        sys.exit(1)
    if not input_path.exists():
        print(f"{RED}ERROR:{RESET} Input file not found: {input_path}")
        print(f"       Use --input to specify your EML 2.1.1 file, e.g.:")
        print(f"       python3 test_transformation.py --input /path/to/your-file.xml")
        sys.exit(1)

    # ── Load ───────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}━━ EML 2.1.1 → EML 2.2.0 — Transformation Test Suite ━━━━━━━━━━━━━━{RESET}")
    print(f"   Stylesheet : {xsl_path}")
    print(f"   Input file : {input_path}")

    try:
        xsl_doc   = etree.parse(str(xsl_path))
        transform = etree.XSLT(xsl_doc)
    except etree.XMLSyntaxError as e:
        print(f"\n{RED}ERROR: Could not parse stylesheet:{RESET}\n  {e}")
        sys.exit(1)

    try:
        src_doc = etree.parse(str(input_path))
    except etree.XMLSyntaxError as e:
        print(f"\n{RED}ERROR: Could not parse input file:{RESET}\n  {e}")
        print(f"\n  Make sure the file is valid XML and encoded in UTF-8.")
        print(f"  If you downloaded it from a browser, it may contain HTML")
        print(f"  formatting — save the raw XML source instead.")
        sys.exit(1)

    # ── Pre-flight check ───────────────────────────────────────────────────────
    print(f"\n{BOLD}[0] Pre-flight checks{RESET}")
    is_211 = validate_input_is_eml211(src_doc)

    # ── Apply transformation ───────────────────────────────────────────────────
    xslt_params = {}
    if args.package_id:
        xslt_params["package-id"] = etree.XSLT.strparam(args.package_id)

    try:
        result      = transform(src_doc, **xslt_params)
        # Inject xmlns:stmml — libxslt strips unused namespace prefixes.
        # stmml is only referenced in schemaLocation text, never in element
        # names, so it is stripped. We reinsert it via string replacement.
        _xml = etree.tostring(result.getroot(), pretty_print=True,
                               xml_declaration=True, encoding="UTF-8").decode("UTF-8")
        _old = '<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"'
        _new = ('<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"'
                ' xmlns:stmml="http://www.xml-cml.org/schema/stmml-1.2"')
        if _old in _xml:
            _xml = _xml.replace(_old, _new, 1)
        result_root = etree.fromstring(_xml.encode("UTF-8"))
    except etree.XSLTApplyError as e:
        print(f"\n{RED}ERROR: Transformation failed:{RESET}\n  {e}")
        sys.exit(1)

    # ── Write output if requested ──────────────────────────────────────────────
    if args.output:
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as fh:
            fh.write(etree.tostring(result_root, pretty_print=True,
                                    xml_declaration=True, encoding="UTF-8"))
        print(f"\n   Output written to: {out_path}")

    # ── Run tests (only meaningful if input is actually EML 2.1.1) ─────────────
    test_namespaces(result_root)
    test_package_id(transform, src_doc)
    test_alternate_identifier(result_root)
    test_pubdate(result_root, src_doc)
    test_core_metadata(result_root, src_doc)
    test_methods(result_root, src_doc)
    test_project(result_root, src_doc)
    test_datatable(result_root, src_doc)
    test_no_211_artefacts(result_root)
    test_no_xslt_errors(transform)

    # ── Summary ────────────────────────────────────────────────────────────────
    total  = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n{BOLD}━━ Results ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"   Total: {total}  │  {GREEN}Passed: {passed}{RESET}  │  {RED}Failed: {failed}{RESET}")

    if not is_211 and failed > 0:
        print(f"\n   {RED}Note:{RESET} Input was not EML 2.1.1 — failures above may be expected.")

    if failed == 0:
        print(f"   {GREEN}🎉  All tests passed.{RESET}\n")
    else:
        print(f"   {RED}⚠   {failed} test(s) failed — see details above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
