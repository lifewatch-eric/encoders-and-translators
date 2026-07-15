#!/usr/bin/env python3
"""
transformations/ISO19139_to_EOSC/test_transformation.py
=============================================================
Automated test suite for the ISO 19139 → EOSC Service transformation.

Requirements:
    pip install lxml

Usage:
    python3 test_transformation.py
    python3 test_transformation.py --input examples/input/your-file.xml
    python3 test_transformation.py --input your-file.xml --output result.json

Returns exit code 0 on all-pass, 1 on any failure.
"""

import sys
import json
import argparse
from pathlib import Path
from lxml import etree

HERE        = Path(__file__).parent.resolve()
DEFAULT_XSL = HERE / "xslt" / "main.xsl"
DEFAULT_IN  = HERE / "examples" / "input" / "semantic-platform-service-iso19139.xml"

NS = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
}

GMD_NS = "http://www.isotc211.org/2005/gmd"
GREEN  = "\033[32m"; RED = "\033[31m"; BOLD = "\033[1m"; RESET = "\033[0m"

results: list[bool] = []


def check(label: str, got=None, expected=None, truthy=None):
    ok = True; detail = ""
    if truthy is not None:
        if not truthy: ok = False; detail = "\n       condition is falsy"
    elif expected is not None:
        if got != expected:
            ok = False; detail = f"\n       got:      {repr(got)}\n       expected: {repr(expected)}"
    results.append(ok)
    icon = f"{GREEN}✅ PASS{RESET}" if ok else f"{RED}❌ FAIL{RESET}"
    print(f"  {icon}  {label}{detail}")


def char_string(element, path):
    text = element.findtext(path, namespaces=NS)
    return (text or "").strip()


# ──────────────────────────────────────────────────────────────────────────────
def test_valid_json(text):
    print(f"\n{BOLD}[1] Output is valid JSON{RESET}")
    try:
        obj = json.loads(text)
        check("json.loads() succeeds", truthy=True)
        return obj
    except json.JSONDecodeError as e:
        check("json.loads() succeeds", truthy=False)
        print(f"       {RED}{e}{RESET}")
        return None


def test_no_id_field(obj):
    print(f"\n{BOLD}[2] \"id\" is never emitted (EOSC assigns it on registration){RESET}")
    check("no top-level 'id' key", truthy="id" not in obj)


def test_name(obj, src):
    print(f"\n{BOLD}[3] name ← citation/title{RESET}")
    expected = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString")
    check("name matches source citation title", got=obj.get("name"), expected=expected)


def test_description(obj, src):
    print(f"\n{BOLD}[4] description ← abstract{RESET}")
    expected = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString")
    check("description matches source abstract", got=obj.get("description"), expected=expected)


def test_publishing_date(obj, src):
    print(f"\n{BOLD}[5] publishingDate ← citation date[publication] or dateStamp fallback{RESET}")
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
    check("publishingDate matches expected source date", got=obj.get("publishingDate"), expected=expected)


def test_type_is_service(obj):
    print(f"\n{BOLD}[6] type is always \"Service\"{RESET}")
    check("type == 'Service'", got=obj.get("type"), expected="Service")


def test_public_contacts(obj, src):
    print(f"\n{BOLD}[7] publicContact ← every distinct electronicMailAddress{RESET}")
    src_emails = sorted(set(
        (e.text or "").strip()
        for e in src.findall(".//gmd:electronicMailAddress/gco:CharacterString", namespaces=NS)
        if (e.text or "").strip()
    ))
    check("publicContact count matches distinct source emails",
          got=sorted(obj.get("publicContact", [])), expected=src_emails)


def test_urls_include_landing_page(obj, src):
    print(f"\n{BOLD}[8] url[0] is the catalogue landing page{RESET}")
    file_id = char_string(src, "gmd:fileIdentifier/gco:CharacterString")
    urls = obj.get("url", [])
    check("url is non-empty", truthy=len(urls) > 0)
    if urls and file_id:
        check("url[0] embeds the fileIdentifier", truthy=file_id in urls[0])


def test_alternative_pids_are_doi_only(obj, src):
    print(f"\n{BOLD}[9] alternativePIDs ← online resources with protocol=DOI{RESET}")
    doi_onlines = [
        o for o in src.findall(
            "gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource",
            namespaces=NS)
        if char_string(o, "gmd:protocol/gco:CharacterString") == "DOI"
    ]
    pids = obj.get("alternativePIDs", [])
    check(f"alternativePIDs count = {len(doi_onlines)}", got=len(pids), expected=len(doi_onlines))
    check("every alternativePID has pidSchema 'DOI'",
          truthy=all(p.get("pidSchema") == "DOI" for p in pids))


def test_tags(obj, src):
    print(f"\n{BOLD}[10] tags ← descriptiveKeywords/MD_Keywords/keyword{RESET}")
    src_kw = sorted(set(
        (k.text or "").strip()
        for k in src.findall(".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString", namespaces=NS)
        if (k.text or "").strip()
    ))
    check("tags match distinct source keywords", got=sorted(obj.get("tags", [])), expected=src_kw)


def test_trl(obj, src):
    print(f"\n{BOLD}[11] trl ← LW_ServiceTRL_service/@codeListValue{RESET}")
    node = src.find(".//gmd:serviceTRL_service/gmd:LW_ServiceTRL_service", namespaces=NS)
    trl = obj.get("trl", "")
    if node is not None:
        code = node.get("codeListValue") or ""
        check("trl is non-empty when source has a TRL code", truthy=bool(trl))
        check("trl follows 'trl-<n>' convention", truthy=trl.startswith("trl-"))
        if "TRL " in code:
            digits = code.split("TRL ", 1)[1].split(" ", 1)[0]
            check("trl number matches source code", got=trl, expected=f"trl-{digits}")
    else:
        check("trl is empty string when source has no TRL code", got=trl, expected="")


def test_categories_and_scientific_domains_present(obj):
    print(f"\n{BOLD}[12] categories (array) / scientificDomains (object) — per service.schema.json{RESET}")
    check("categories has exactly one entry", got=len(obj.get("categories", [])), expected=1)
    if obj.get("categories"):
        cat = obj["categories"][0]
        check("category id present", truthy=bool(cat.get("category")))
        check("subcategory id present", truthy=bool(cat.get("subcategory")))
    sd = obj.get("scientificDomains")
    check("scientificDomains is a plain object, not an array", truthy=isinstance(sd, dict))
    if isinstance(sd, dict):
        check("scientificDomain present", truthy=bool(sd.get("scientificDomain")))
        check("scientificSubdomain present", truthy=bool(sd.get("scientificSubdomain")))


def test_fixed_defaults(obj):
    print(f"\n{BOLD}[13] Fixed-default fields{RESET}")
    check("accessType has a value", truthy=bool(obj.get("accessType")))
    check("jurisdiction has a value", truthy=bool(obj.get("jurisdiction")))
    check("nodePID has a value", truthy=bool(obj.get("nodePID")))
    check("logo is a URL", truthy=(obj.get("logo") or "").startswith("http"))


def test_webpage_differs_from_url(obj, src):
    print(f"\n{BOLD}[13b] webpage uses a different landing-page pattern than url[0]{RESET}")
    file_id = char_string(src, "gmd:fileIdentifier/gco:CharacterString")
    webpage = obj.get("webpage", "")
    urls = obj.get("url", [])
    check("webpage is not identical to url[0]",
          truthy=bool(urls) and webpage != urls[0])
    check("webpage embeds the fileIdentifier", truthy=file_id in webpage)
    check("webpage uses the catalogue-search UI pattern, not the API pattern",
          truthy="catalog.search" in webpage and "srv/api/records" not in webpage)


def test_field_names_match_real_eosc_schema(obj):
    print(f"\n{BOLD}[14] Field names match the real EOSC schema (not the source sheet's own typos){RESET}")
    check("uses 'url', not 'urls'", truthy="url" in obj and "urls" not in obj)
    check("uses 'publicContact', not 'publicContacts'", truthy="publicContact" in obj and "publicContacts" not in obj)
    check("uses 'accessType', not 'accessTypes'", truthy="accessType" in obj and "accessTypes" not in obj)
    check("no top-level 'id' key", truthy="id" not in obj)


def test_no_xslt_errors(transform_errors):
    print(f"\n{BOLD}[15] XSLT processor health{RESET}")
    check("No XSLT processor errors or warnings", truthy=len(transform_errors) == 0)
    for e in transform_errors:
        print(f"       {RED}{e}{RESET}")


# ──────────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Test ISO 19139 → EOSC Service transformation.")
    p.add_argument("--input",  "-i", type=Path, default=DEFAULT_IN)
    p.add_argument("--xsl",          type=Path, default=DEFAULT_XSL)
    p.add_argument("--output", "-o", type=Path, default=None)
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

    print(f"\n{BOLD}━━ ISO 19139 → EOSC Service — Test Suite ━━━━━━━━━━━━━━━━━━━━━{RESET}")
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

    print(f"\n{BOLD}[0] Pre-flight{RESET}")
    if src_doc.getroot().tag == f"{{{GMD_NS}}}MD_Metadata":
        print(f"  {GREEN}✅{RESET}  Input confirmed as ISO 19139 (gmd:MD_Metadata)")
    else:
        print(f"  {RED}⚠  Input root: {src_doc.getroot().tag!r} — expected gmd:MD_Metadata{RESET}")

    t = etree.XSLT(xsl_doc)
    result = t(src_doc)
    text = str(result)

    if args.output:
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="UTF-8")
        print(f"\n   Output written to: {out_path}")

    src_root = src_doc.getroot()
    obj = test_valid_json(text)

    if obj is not None:
        test_no_id_field(obj)
        test_name(obj, src_root)
        test_description(obj, src_root)
        test_publishing_date(obj, src_root)
        test_type_is_service(obj)
        test_public_contacts(obj, src_root)
        test_urls_include_landing_page(obj, src_root)
        test_alternative_pids_are_doi_only(obj, src_root)
        test_tags(obj, src_root)
        test_trl(obj, src_root)
        test_categories_and_scientific_domains_present(obj)
        test_fixed_defaults(obj)
        test_webpage_differs_from_url(obj, src_root)
        test_field_names_match_real_eosc_schema(obj)
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
