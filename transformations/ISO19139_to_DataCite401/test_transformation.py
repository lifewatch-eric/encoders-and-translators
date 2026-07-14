#!/usr/bin/env python3
"""
transformations/ISO19139_to_DataCite401/test_transformation.py
=============================================================
Automated test suite for the ISO 19139 → DataCite 4.0.1 (OpenAIRE) transformation.

Requirements:
    pip install lxml

Usage:
    python3 test_transformation.py
    python3 test_transformation.py --input examples/input/your-file.xml --resource-type VRE
    python3 test_transformation.py --input your-file.xml --output result.xml

Returns exit code 0 on all-pass, 1 on any failure.
"""

import sys
import argparse
from pathlib import Path
from lxml import etree

HERE        = Path(__file__).parent.resolve()
DEFAULT_XSL = HERE / "xslt" / "main.xsl"
DEFAULT_IN  = HERE / "examples" / "input" / "crustaceans-workflow-iso19139.xml"

NS = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "datacite": "http://datacite.org/schema/kernel-4",
    "oaire": "http://namespace.openaire.eu/schema/oaire/",
}

GMD_NS = "http://www.isotc211.org/2005/gmd"
GREEN  = "\033[32m"; RED = "\033[31m"; BOLD = "\033[1m"; RESET = "\033[0m"

results: list[bool] = []

ROLE_TABLE = {
    "author": "creator", "creator": "creator", "owner": "creator",
    "associatedparty": "contributor:RelatedPerson",
    "custodian": "contributor:DataManager",
    "distributor": "contributor:Distributor",
    "pointofcontact": "contributor:ContactPerson",
    "principalinvestigator": "contributor:Supervisor",
    "processor": "contributor:DataCurator",
    "resourceprovider": "contributor:Producer",
    "user": "contributor:Researcher",
}


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


def role_target(role_code: str) -> str:
    key = "".join(role_code.lower().split())
    return ROLE_TABLE.get(key, "contributor:Other")


# ──────────────────────────────────────────────────────────────────────────────
def test_root_is_oaire_resource(root):
    print(f"\n{BOLD}[1] Root element is oaire:resource{RESET}")
    check("root tag", got=etree.QName(root).localname, expected="resource")
    check("root namespace", got=etree.QName(root).namespace,
          expected="http://namespace.openaire.eu/schema/oaire/")


def test_identifier(root, src):
    print(f"\n{BOLD}[2] datacite:identifier — DOI if present, else URL fallback{RESET}")
    onlines = src.findall(
        "gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource",
        namespaces=NS)
    doi_online = None
    for o in onlines:
        protocol = char_string(o, "gmd:protocol/gco:CharacterString")
        url = char_string(o, "gmd:linkage/gmd:URL")
        if protocol == "DOI" or "doi.org" in url:
            doi_online = o
            break
    ident = root.find("datacite:identifier", namespaces=NS)
    check("datacite:identifier is present", truthy=ident is not None)
    if ident is not None:
        if doi_online is not None:
            check("identifierType is DOI", got=ident.get("identifierType"), expected="DOI")
            check("value matches source online DOI URL",
                  got=(ident.text or "").strip(),
                  expected=char_string(doi_online, "gmd:linkage/gmd:URL"))
        else:
            check("identifierType is URL (fallback)", got=ident.get("identifierType"), expected="URL")
            file_id = char_string(src, "gmd:fileIdentifier/gco:CharacterString")
            check("fallback URL embeds fileIdentifier", truthy=file_id in (ident.text or ""))


def test_alternate_identifiers(root, src):
    print(f"\n{BOLD}[3] datacite:alternateIdentifiers ← fileIdentifier (PackageID){RESET}")
    file_id = char_string(src, "gmd:fileIdentifier/gco:CharacterString")
    alt = root.find(
        "datacite:alternateIdentifiers/datacite:alternateIdentifier", namespaces=NS)
    check("alternateIdentifier present", truthy=alt is not None)
    if alt is not None:
        check("alternateIdentifierType is PackageID", got=alt.get("alternateIdentifierType"), expected="PackageID")
        check("value matches fileIdentifier", got=(alt.text or "").strip(), expected=file_id)


def test_title(root, src):
    print(f"\n{BOLD}[4] datacite:titles/title ← citation/title{RESET}")
    title = root.findtext("datacite:titles/datacite:title", namespaces=NS)
    expected = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString")
    check("title matches source citation title", got=(title or "").strip(), expected=expected)


def test_publisher(root):
    print(f"\n{BOLD}[5] datacite:publisher{RESET}")
    check("publisher present", truthy=bool(root.findtext("datacite:publisher", namespaces=NS)))


def test_publication_year_and_dates(root, src):
    print(f"\n{BOLD}[6] datacite:publicationYear / datacite:dates ← publication-typed citation date{RESET}")
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
    if expected:
        check("publicationYear matches first 4 chars of publication date",
              got=root.findtext("datacite:publicationYear", namespaces=NS), expected=expected[:4])
        issued = root.find("datacite:dates/datacite:date[@dateType='Issued']", namespaces=NS)
        check("datacite:date[Issued] present", truthy=issued is not None)
        if issued is not None:
            check("Issued date matches source", got=(issued.text or "").strip(), expected=expected)


def test_description(root, src):
    print(f"\n{BOLD}[7] datacite:descriptions ← abstract{RESET}")
    expected = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString")
    desc = root.findtext("datacite:descriptions/datacite:description", namespaces=NS)
    if expected:
        check("description matches source abstract", got=(desc or "").strip(), expected=expected)


def test_subjects(root, src):
    print(f"\n{BOLD}[8] datacite:subjects ← descriptiveKeywords/keyword{RESET}")
    src_kw = [
        (k.text or "").strip()
        for k in src.findall(
            ".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString", namespaces=NS)
    ]
    out_kw = [(s.text or "").strip() for s in root.findall("datacite:subjects/datacite:subject", namespaces=NS)]
    check("subject count matches source keyword count", got=len(out_kw), expected=len(src_kw))
    check("subject values match source keywords (order preserved)", got=out_kw, expected=src_kw)


def test_creators_and_contributors(root, src):
    print(f"\n{BOLD}[9] datacite:creators / datacite:contributors ← CI_ResponsibleParty role routing{RESET}")
    parties = src.findall(".//gmd:CI_ResponsibleParty", namespaces=NS)
    expected_creators = 0
    expected_contrib_types = []
    for p in parties:
        role_node = p.find("gmd:role/gmd:CI_RoleCode", namespaces=NS)
        role = (role_node.get("codeListValue") or "") if role_node is not None else ""
        target = role_target(role)
        if target == "creator":
            expected_creators += 1
        else:
            expected_contrib_types.append(target.split(":", 1)[1])

    creators = root.findall("datacite:creators/datacite:creator", namespaces=NS)
    contributors = root.findall("datacite:contributors/datacite:contributor", namespaces=NS)
    check(f"creator count = {expected_creators}", got=len(creators), expected=expected_creators)
    check(f"contributor count = {len(expected_contrib_types)}", got=len(contributors), expected=len(expected_contrib_types))
    if contributors:
        got_types = [c.get("contributorType") for c in contributors]
        check("contributorType values match expected role routing",
              got=got_types, expected=expected_contrib_types)
    if creators:
        name = creators[0].findtext("datacite:creatorName", namespaces=NS)
        check("first creatorName is in 'Family, Given' form", truthy=bool(name) and "," in (name or ""))


def test_rights_list(root, src):
    print(f"\n{BOLD}[10] datacite:rightsList ← useLimitation{RESET}")
    license_text = char_string(
        src, "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString")
    rights = root.find("datacite:rightsList/datacite:rights", namespaces=NS)
    if license_text:
        check("datacite:rights present when source has a license", truthy=rights is not None)
        if rights is not None:
            check("rightsIdentifier matches source license text",
                  got=rights.get("rightsIdentifier"), expected=license_text)
            check("rightsIdentifierScheme is SPDX", got=rights.get("rightsIdentifierScheme"), expected="SPDX")
    else:
        check("no rightsList emitted when source has no license", truthy=rights is None)


def test_resource_type(root, resource_type):
    print(f"\n{BOLD}[11] resourceType pair ← $resource-type parameter ({resource_type}){RESET}")
    dc_type = root.find("datacite:resourceType", namespaces=NS)
    oaire_type = root.find("oaire:resourceType", namespaces=NS)
    check("datacite:resourceType present", truthy=dc_type is not None)
    check("oaire:resourceType present", truthy=oaire_type is not None)
    if dc_type is not None:
        expected = "InteractiveResource" if resource_type.lower() == "vre" else "Workflow"
        check("datacite:resourceType/@resourceTypeGeneral matches parameter",
              got=dc_type.get("resourceTypeGeneral"), expected=expected)


def test_no_unmapped_fields_invented(root):
    print(f"\n{BOLD}[12] Fields the source sheet marks \"Not mapped\" are absent{RESET}")
    # creation date / revision date / status have no DataCite equivalent emitted
    # by this stylesheet — only one datacite:dates/date[@dateType='Issued'] should exist.
    dates = root.findall("datacite:dates/datacite:date", namespaces=NS)
    check("at most one datacite:date is emitted (Issued only)", truthy=len(dates) <= 1)


def test_no_xslt_errors(transform_errors):
    print(f"\n{BOLD}[13] XSLT processor health{RESET}")
    check("No XSLT processor errors or warnings", truthy=len(transform_errors) == 0)
    for e in transform_errors:
        print(f"       {RED}{e}{RESET}")


# ──────────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Test ISO 19139 → DataCite 4.0.1 transformation.")
    p.add_argument("--input",  "-i", type=Path, default=DEFAULT_IN)
    p.add_argument("--xsl",          type=Path, default=DEFAULT_XSL)
    p.add_argument("--output", "-o", type=Path, default=None)
    p.add_argument("--resource-type", default="Workflow", choices=["Workflow", "VRE"])
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

    print(f"\n{BOLD}━━ ISO 19139 → DataCite 4.0.1 — Test Suite ━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"   Stylesheet    : {xsl_path}")
    print(f"   Input file    : {input_path}")
    print(f"   resource-type : {args.resource_type}")

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
    params = {"resource-type": etree.XSLT.strparam(args.resource_type)}
    result = t(src_doc, **params)
    root   = result.getroot()

    if args.output:
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(etree.tostring(root, pretty_print=True,
                                   xml_declaration=True, encoding="UTF-8"))
        print(f"\n   Output written to: {out_path}")

    src_root = src_doc.getroot()

    test_root_is_oaire_resource(root)
    test_identifier(root, src_root)
    test_alternate_identifiers(root, src_root)
    test_title(root, src_root)
    test_publisher(root)
    test_publication_year_and_dates(root, src_root)
    test_description(root, src_root)
    test_subjects(root, src_root)
    test_creators_and_contributors(root, src_root)
    test_rights_list(root, src_root)
    test_resource_type(root, args.resource_type)
    test_no_unmapped_fields_invented(root)
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
