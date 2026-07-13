#!/usr/bin/env python3
"""
transformations/ISO19139_to_EML220/test_transformation.py
=============================================================
Automated test suite for the ISO 19139 → EML 2.2.0 transformation.

Requirements:
    pip install lxml

Usage:
    python3 test_transformation.py
    python3 test_transformation.py --input examples/input/your-file.xml
    python3 test_transformation.py --input your-file.xml --output result.xml

Returns exit code 0 on all-pass, 1 on any failure.
"""

import sys
import argparse
from pathlib import Path
from lxml import etree

HERE        = Path(__file__).parent.resolve()
DEFAULT_XSL = HERE / "xslt" / "main.xsl"
DEFAULT_IN  = HERE / "examples" / "input" / "lesina-phytoplankton-iso19139.xml"

# Namespace map for XPath queries on the ISO 19139 source. Note: per this
# repo's EML convention (see EML211_to_EML220 / EML220_to_DataCite401
# examples), the output eml:eml root is namespace-qualified but everything
# under <dataset> is NOT — so output queries below use plain, unprefixed
# element names.
NS = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "gml": "http://www.opengis.net/gml",
}

GMD_NS = "http://www.isotc211.org/2005/gmd"
GREEN  = "\033[32m"; RED = "\033[31m"; BOLD = "\033[1m"; RESET = "\033[0m"

results: list[bool] = []


def check(label: str, got=None, expected=None, contains: str = None,
          not_contains: str = None, truthy=None):
    ok = True; detail = ""
    if truthy is not None:
        if not truthy: ok = False; detail = "\n       condition is falsy"
    elif expected is not None:
        if got != expected:
            ok = False; detail = f"\n       got:      {repr(got)}\n       expected: {repr(expected)}"
    if contains is not None and contains not in (got or ""):
        ok = False; detail = f"\n       '{contains}' not found in value"
    if not_contains is not None and not_contains in (got or ""):
        ok = False; detail = f"\n       '{not_contains}' unexpectedly found"
    results.append(ok)
    icon = f"{GREEN}✅ PASS{RESET}" if ok else f"{RED}❌ FAIL{RESET}"
    print(f"  {icon}  {label}{detail}")


def role_code(rp_element):
    """Return the gmd:role/gmd:CI_RoleCode/@codeListValue for a CI_ResponsibleParty, or ''."""
    node = rp_element.find("gmd:role/gmd:CI_RoleCode", namespaces=NS)
    return (node.get("codeListValue") or "").strip().lower() if node is not None else ""


def char_string(element, path):
    """normalize-space() text of a gco:CharacterString reached via `path`, or ''."""
    text = element.findtext(path, namespaces=NS)
    return (text or "").strip()


def apply_transform(xsl_doc, src_doc, params=None):
    t = etree.XSLT(xsl_doc)
    p = {k: etree.XSLT.strparam(v) for k, v in (params or {}).items()}
    return t(src_doc, **p).getroot()


# ──────────────────────────────────────────────────────────────────────────────
def test_package_id(root, src):
    print(f"\n{BOLD}[1] eml:eml/@packageId ← gmd:fileIdentifier{RESET}")
    file_id = char_string(src, "gmd:fileIdentifier/gco:CharacterString")
    pkg = root.get("packageId")
    check("packageId is present", truthy=bool(pkg))
    if file_id:
        check("packageId matches gmd:fileIdentifier", got=pkg, expected=file_id)


def test_title(root, src):
    print(f"\n{BOLD}[2] dataset/title{RESET}")
    title = root.findtext("dataset/title")
    src_title = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString")
    check("title is present", truthy=bool(title))
    check("title matches source citation title", got=(title or "").strip(), expected=src_title)


def test_creators(root, src):
    print(f"\n{BOLD}[3] dataset/creator ← citedResponsibleParty[role=originator|author]{RESET}")
    creators = root.findall("dataset/creator")
    src_parties = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty",
        namespaces=NS)
    expected_creators = [p for p in src_parties if role_code(p) in ("originator", "author")]
    check(f"creator count = {len(expected_creators)}", got=len(creators), expected=len(expected_creators))


def test_associated_party(root, src):
    print(f"\n{BOLD}[4] dataset/associatedParty ← non-originator citedResponsibleParty{RESET}")
    assoc = root.findall("dataset/associatedParty")
    src_parties = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty",
        namespaces=NS)
    non_creator = [p for p in src_parties if role_code(p) not in ("originator", "author")]
    check(f"associatedParty count = {len(non_creator)}", got=len(assoc), expected=len(non_creator))
    if assoc:
        role_texts = [a.findtext("role") for a in assoc]
        check("associatedParty carries a non-empty <role>", truthy=all(bool(r) for r in role_texts))


def test_metadata_provider(root, src):
    print(f"\n{BOLD}[5] dataset/metadataProvider ← top-level gmd:contact{RESET}")
    providers = root.findall("dataset/metadataProvider")
    src_contacts = src.findall("gmd:contact/gmd:CI_ResponsibleParty", namespaces=NS)
    check(f"metadataProvider count = {len(src_contacts)}", got=len(providers), expected=len(src_contacts))


def test_pub_date(root, src):
    print(f"\n{BOLD}[6] dataset/pubDate{RESET}")
    pub_date = root.findtext("dataset/pubDate")
    pub_dates = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date",
        namespaces=NS)
    expected = None
    for d in pub_dates:
        code_node = d.find("gmd:dateType/gmd:CI_DateTypeCode", namespaces=NS)
        code_val = (code_node.get("codeListValue") or "").lower() if code_node is not None else ""
        if code_val == "publication":
            expected = char_string(d, "gmd:date/gco:Date")
            break
    if expected is None:
        expected = char_string(src, "gmd:dateStamp/gco:Date")
    if expected:
        check("pubDate present", truthy=bool(pub_date))
        check("pubDate matches expected source date", got=(pub_date or "").strip(), expected=expected)
    else:
        check("no pubDate emitted when source has no date", truthy=pub_date is None)


def test_no_empty_pubdate(root):
    print(f"\n{BOLD}[6b] pubDate guard — never empty{RESET}")
    pub_node = root.find("dataset/pubDate")
    if pub_node is not None:
        check("pubDate text is non-empty", truthy=bool((pub_node.text or "").strip()))


def test_language(root, src):
    print(f"\n{BOLD}[7] dataset/language — ISO code → full word{RESET}")
    lang = root.findtext("dataset/language")
    lang_node = src.find(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:language/gmd:LanguageCode", namespaces=NS)
    if lang_node is None:
        # Falls back to the top-level MD_Metadata/language when the
        # identification block doesn't carry its own.
        lang_node = src.find("gmd:language/gmd:LanguageCode", namespaces=NS)
    code_val = lang_node.get("codeListValue") if lang_node is not None else None
    if code_val:
        check("language element present", truthy=bool(lang))
        check("language is not the raw 3-letter code (word expansion applied for known codes)",
              truthy=(lang != code_val) or len(code_val) > 3)


def test_abstract(root, src):
    print(f"\n{BOLD}[8] dataset/abstract/para{RESET}")
    para = root.findtext("dataset/abstract/para")
    src_abs = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString")
    if src_abs:
        check("abstract/para present", truthy=bool(para))
        check("abstract text matches source", got=(para or "").strip(), expected=src_abs)


def test_keywords(root, src):
    print(f"\n{BOLD}[9] dataset/keywordSet{RESET}")
    sets = root.findall("dataset/keywordSet")
    src_sets = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords",
        namespaces=NS)
    check(f"keywordSet count = {len(src_sets)}", got=len(sets), expected=len(src_sets))
    for i, (src_set, out_set) in enumerate(zip(src_sets, sets)):
        src_kw = src_set.findall("gmd:keyword/gco:CharacterString", namespaces=NS)
        out_kw = out_set.findall("keyword")
        check(f"keywordSet[{i+1}] keyword count matches", got=len(out_kw), expected=len(src_kw))
        thesaurus = char_string(
            src_set, "gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString")
        out_thesaurus = out_set.findtext("keywordThesaurus")
        if thesaurus:
            check(f"keywordSet[{i+1}] thesaurus name preserved",
                  got=(out_thesaurus or "").strip(), expected=thesaurus)
        else:
            check(f"keywordSet[{i+1}] keywordThesaurus='none' when no thesaurusName",
                  got=out_thesaurus, expected="none")


def test_intellectual_rights(root, src):
    print(f"\n{BOLD}[10] dataset/intellectualRights{RESET}")
    src_limits = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/*/gmd:useLimitation/gco:CharacterString",
        namespaces=NS)
    paras = root.findall("dataset/intellectualRights/para")
    check(f"intellectualRights/para count = {len(src_limits)}", got=len(paras), expected=len(src_limits))


def test_distribution(root, src):
    print(f"\n{BOLD}[11] dataset/distribution/online{RESET}")
    src_onlines = [
        o for o in src.findall(
            "gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource",
            namespaces=NS)
        if char_string(o, "gmd:linkage/gmd:URL")
    ]
    online = root.findall("dataset/distribution/online")
    check(f"online count = {len(src_onlines)}", got=len(online), expected=len(src_onlines))
    if online and src_onlines:
        url = online[0].findtext("url")
        src_url = char_string(src_onlines[0], "gmd:linkage/gmd:URL")
        check("first online url matches source linkage", got=(url or "").strip(), expected=src_url)


def test_coverage_geographic(root, src):
    print(f"\n{BOLD}[12] dataset/coverage/geographicCoverage{RESET}")
    src_boxes = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox",
        namespaces=NS)
    boxes = root.findall("dataset/coverage/geographicCoverage")
    check(f"geographicCoverage count = {len(src_boxes)}", got=len(boxes), expected=len(src_boxes))
    if boxes and src_boxes:
        bc = boxes[0].find("boundingCoordinates")
        west = bc.findtext("westBoundingCoordinate")
        src_west = char_string(src_boxes[0], "gmd:westBoundLongitude/gco:Decimal")
        check("westBoundingCoordinate matches source westBoundLongitude",
              got=(west or "").strip(), expected=src_west)


def test_coverage_temporal(root, src):
    print(f"\n{BOLD}[13] dataset/coverage/temporalCoverage{RESET}")
    src_extents = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent",
        namespaces=NS)
    temporal = root.findall("dataset/coverage/temporalCoverage")
    check(f"temporalCoverage count = {len(src_extents)}", got=len(temporal), expected=len(src_extents))
    for i, (src_ext, out_ext) in enumerate(zip(src_extents, temporal)):
        if src_ext.find("gmd:extent/gml:TimePeriod", namespaces=NS) is not None:
            check(f"temporalCoverage[{i+1}] uses rangeOfDates for gml:TimePeriod",
                  truthy=out_ext.find("rangeOfDates") is not None)
        elif src_ext.find("gmd:extent/gml:TimeInstant", namespaces=NS) is not None:
            check(f"temporalCoverage[{i+1}] uses singleDateTime for gml:TimeInstant",
                  truthy=out_ext.find("singleDateTime") is not None)


def test_contact(root, src):
    print(f"\n{BOLD}[14] dataset/contact ← MD_DataIdentification/pointOfContact{RESET}")
    src_contacts = src.findall(
        "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty",
        namespaces=NS)
    contacts = root.findall("dataset/contact")
    check(f"contact count = {len(src_contacts)}", got=len(contacts), expected=len(src_contacts))


def test_element_order(root):
    print(f"\n{BOLD}[15] EML 2.2.0 resourceGroup element ordering{RESET}")
    dataset = root.find("dataset")
    allowed_order = [
        "alternateIdentifier", "title", "creator", "metadataProvider", "associatedParty",
        "pubDate", "language", "abstract", "keywordSet", "intellectualRights",
        "distribution", "coverage", "contact",
    ]
    seen_indices = []
    for child in dataset:
        tag = etree.QName(child).localname
        if tag in allowed_order:
            seen_indices.append(allowed_order.index(tag))
    check("dataset children appear in non-decreasing schema order",
          truthy=seen_indices == sorted(seen_indices))


def test_no_xslt_errors(transform_errors):
    print(f"\n{BOLD}[16] XSLT processor health{RESET}")
    check("No XSLT processor errors or warnings", truthy=len(transform_errors) == 0)
    for e in transform_errors:
        print(f"       {RED}{e}{RESET}")


# ──────────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Test ISO 19139 → EML 2.2.0 transformation.")
    p.add_argument("--input",  "-i", type=Path, default=DEFAULT_IN)
    p.add_argument("--xsl",          type=Path, default=DEFAULT_XSL)
    p.add_argument("--output", "-o", type=Path, default=None)
    p.add_argument("--package-id",   default=None)
    return p.parse_args()


def main():
    args = parse_args()
    xsl_path   = args.xsl.resolve()
    input_path = args.input.resolve()

    if not xsl_path.exists():
        print(f"{RED}ERROR:{RESET} Stylesheet not found: {xsl_path}"); sys.exit(1)
    if not input_path.exists():
        print(f"{RED}ERROR:{RESET} Input file not found: {input_path}")
        print(f"  Use --input to specify your ISO 19139 file."); sys.exit(1)

    print(f"\n{BOLD}━━ ISO 19139 → EML 2.2.0 — Test Suite ━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"   Stylesheet : {xsl_path}")
    print(f"   Input file : {input_path}")

    try:
        xsl_doc = etree.parse(str(xsl_path))
    except etree.XMLSyntaxError as e:
        print(f"{RED}ERROR: Cannot parse stylesheet:{RESET}\n  {e}"); sys.exit(1)

    try:
        src_doc = etree.parse(str(input_path))
    except etree.XMLSyntaxError as e:
        print(f"{RED}ERROR: Cannot parse input file:{RESET}\n  {e}"); sys.exit(1)

    # Check input is ISO 19139
    print(f"\n{BOLD}[0] Pre-flight{RESET}")
    if src_doc.getroot().tag == f"{{{GMD_NS}}}MD_Metadata":
        print(f"  {GREEN}✅{RESET}  Input confirmed as ISO 19139 (gmd:MD_Metadata)")
    else:
        print(f"  {RED}⚠  Input root: {src_doc.getroot().tag!r} — expected gmd:MD_Metadata{RESET}")

    # Run transformation
    t = etree.XSLT(xsl_doc)
    params = {}
    if args.package_id:
        params["package-id"] = etree.XSLT.strparam(args.package_id)
    result = t(src_doc, **params)
    root   = result.getroot()

    # Save output if requested
    if args.output:
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(etree.tostring(root, pretty_print=True,
                                   xml_declaration=True, encoding="UTF-8"))
        print(f"\n   Output written to: {out_path}")

    src_root = src_doc.getroot()

    # Run all test groups
    test_package_id(root, src_root)
    test_title(root, src_root)
    test_creators(root, src_root)
    test_associated_party(root, src_root)
    test_metadata_provider(root, src_root)
    test_pub_date(root, src_root)
    test_no_empty_pubdate(root)
    test_language(root, src_root)
    test_abstract(root, src_root)
    test_keywords(root, src_root)
    test_intellectual_rights(root, src_root)
    test_distribution(root, src_root)
    test_coverage_geographic(root, src_root)
    test_coverage_temporal(root, src_root)
    test_contact(root, src_root)
    test_element_order(root)
    test_no_xslt_errors(t.error_log)

    total  = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n{BOLD}━━ Results ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"   Total: {total}  │  {GREEN}Passed: {passed}{RESET}  │  {RED}Failed: {failed}{RESET}")
    if failed == 0:
        print(f"   {GREEN}🎉  All tests passed.{RESET}\n")
    else:
        print(f"   {RED}⚠   {failed} test(s) failed — see details above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
