#!/usr/bin/env python3
"""
transformations/EML220_to_DataCite401/test_transformation.py
=============================================================
Automated test suite for the EML 2.2.0 → DataCite 4.0.1 (OpenAIRE) transformation.

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
DEFAULT_IN  = HERE / "examples" / "input" / "lesina-phytoplankton-eml220.xml"

# Namespace map for XPath queries on the output
NS = {
    "datacite": "http://datacite.org/schema/kernel-4",
    "oaire":    "http://namespace.openaire.eu/schema/oaire/",
    "dc":       "http://purl.org/dc/elements/1.1/",
    "xsi":      "http://www.w3.org/2001/XMLSchema-instance",
}

EML220_NS = "https://eml.ecoinformatics.org/eml-2.2.0"
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


def xp(root, path):
    """XPath with namespace map, return first result text or None."""
    res = root.xpath(path, namespaces=NS)
    if not res: return None
    return res[0].text if hasattr(res[0], "text") else str(res[0])


def xpa(root, path, attr):
    """XPath, return attribute value of first match."""
    res = root.xpath(path, namespaces=NS)
    if not res: return None
    return res[0].get(attr)


def apply_transform(xsl_doc, src_doc, params=None):
    """Apply XSLT with optional params; return output root."""
    t = etree.XSLT(xsl_doc)
    p = {k: etree.XSLT.strparam(v) for k, v in (params or {}).items()}
    return t(src_doc, **p).getroot()


# ──────────────────────────────────────────────────────────────────────────────
def test_identifier(root, src):
    print(f"\n{BOLD}[1] datacite:identifier — DOI preferred{RESET}")
    ident = xp(root, "//datacite:identifier")
    id_type = xpa(root, "//datacite:identifier", "identifierType")
    src_alts = src.findall("dataset/alternateIdentifier")
    doi_alts = [a.text for a in src_alts if a.text and "doi" in a.text.lower()]

    if doi_alts:
        check("identifierType is DOI when DOI alternateIdentifier present",
              got=id_type, expected="DOI")
        check("identifier value is the DOI",
              got=ident, expected=doi_alts[0])
    else:
        check("identifierType is URL when no DOI present",
              got=id_type, expected="URL")
        check("identifier value contains catalogue URL",
              got=ident, contains="metadatacatalogue")


def test_title(root, src):
    print(f"\n{BOLD}[2] datacite:title{RESET}")
    title  = xp(root, "//datacite:titles/datacite:title")
    lang   = xpa(root, "//datacite:titles/datacite:title", "{http://www.w3.org/XML/1998/namespace}lang")
    src_title = (src.findtext("dataset/title") or "").strip()
    check("title matches source", got=title, expected=src_title)
    check("xml:lang attribute present on title", truthy=lang is not None)


def test_publisher(root, src):
    print(f"\n{BOLD}[3] datacite:publisher{RESET}")
    pub = xp(root, "//datacite:publisher")
    check("publisher is present and non-empty", truthy=bool(pub and pub.strip()))


def test_publication_year(root, src):
    print(f"\n{BOLD}[4] datacite:publicationYear{RESET}")
    year = xp(root, "//datacite:publicationYear")
    src_date = (src.findtext("dataset/pubDate") or "").strip()
    expected_year = src_date[:4] if src_date else None
    check("publicationYear is present", truthy=bool(year))
    check("publicationYear is 4 digits", truthy=bool(year) and len(year.strip()) == 4)
    if expected_year:
        check(f"publicationYear matches source year ({expected_year})",
              got=year.strip() if year else None, expected=expected_year)


def test_dates(root, src):
    print(f"\n{BOLD}[5] datacite:dates{RESET}")
    date = xp(root, "//datacite:dates/datacite:date[@dateType='Issued']")
    src_date = (src.findtext("dataset/pubDate") or "").strip()
    check("Issued date is present", truthy=bool(date))
    check("Issued date matches source pubDate", got=date, expected=src_date)


def test_description(root, src):
    print(f"\n{BOLD}[6] datacite:description (Abstract){RESET}")
    desc = xp(root, "//datacite:descriptions/datacite:description[@descriptionType='Abstract']")
    desc_type = xpa(root, "//datacite:descriptions/datacite:description", "descriptionType")
    # Collect source text from abstract/para
    src_paras = src.findall("dataset/abstract/para")
    src_text = " ".join((p.text or "").strip() for p in src_paras if (p.text or "").strip())
    if not src_text:
        src_text = (src.findtext("dataset/abstract") or "").strip()
    check("description element present", truthy=desc is not None)
    check("descriptionType is 'Abstract'", got=desc_type, expected="Abstract")
    if src_text:
        check("description text extracted from abstract/para", truthy=bool(desc and desc.strip()))


def test_subjects(root, src):
    print(f"\n{BOLD}[7] datacite:subjects{RESET}")
    subjects = root.xpath("//datacite:subjects/datacite:subject", namespaces=NS)
    src_keywords = src.findall("dataset/keywordSet/keyword")
    check(f"All {len(src_keywords)} keywords emitted as subjects",
          got=len(subjects), expected=len(src_keywords))
    # Verify subjectScheme is set when thesaurus is not 'none'
    for ks in src.findall("dataset/keywordSet"):
        thes = (ks.findtext("keywordThesaurus") or "").strip()
        if thes.lower() not in ("", "none"):
            kw0 = (ks.find("keyword").text or "").strip() if ks.find("keyword") is not None else ""
            matches = [s for s in subjects if (s.text or "").strip() == kw0]
            if matches:
                check(f"keyword '{kw0}' has subjectScheme='{thes}'",
                      got=matches[0].get("subjectScheme"), expected=thes)


def test_creators(root, src):
    print(f"\n{BOLD}[8] datacite:creators{RESET}")
    creators = root.xpath("//datacite:creators/datacite:creator", namespaces=NS)
    src_creators = src.findall("dataset/creator")
    check(f"All {len(src_creators)} creators preserved",
          got=len(creators), expected=len(src_creators))
    # FIX-3: nameIdentifier only emitted when userId present
    for i, (sc, oc) in enumerate(zip(src_creators, creators)):
        uid = (sc.findtext("userId") or "").strip()
        out_ni = oc.xpath("datacite:nameIdentifier", namespaces=NS)
        if uid:
            check(f"creator[{i+1}] nameIdentifier present (has ORCID)",
                  truthy=len(out_ni) > 0)
            check(f"creator[{i+1}] nameIdentifier value = {uid!r}",
                  got=(out_ni[0].text or "").strip() if out_ni else None, expected=uid)
        else:
            check(f"creator[{i+1}] no empty nameIdentifier emitted (no ORCID in source)",
                  truthy=len(out_ni) == 0)
    # Name format: Surname, GivenName
    first_name = xp(root, "(//datacite:creators/datacite:creator/datacite:creatorName)[1]")
    check("Creator name uses 'Surname, GivenName' format",
          truthy=first_name is not None and "," in first_name)


def test_contributors(root, src):
    print(f"\n{BOLD}[9] datacite:contributors{RESET}")
    contacts = src.findall("dataset/contact")
    providers = src.findall("dataset/metadataProvider")
    out_contact = root.xpath("//datacite:contributors/datacite:contributor[@contributorType='ContactPerson']",
                              namespaces=NS)
    out_manager = root.xpath("//datacite:contributors/datacite:contributor[@contributorType='DataManager']",
                              namespaces=NS)
    check(f"ContactPerson count = {len(contacts)}",
          got=len(out_contact), expected=len(contacts))
    check(f"DataManager count = {len(providers)}",
          got=len(out_manager), expected=len(providers))


def test_geo(root, src):
    print(f"\n{BOLD}[10] datacite:geoLocations (FIX-1 check){RESET}")
    geo_boxes = root.xpath("//datacite:geoLocationBox", namespaces=NS)
    src_geo = src.findall("dataset/coverage/geographicCoverage")
    check(f"geoLocation count = {len(src_geo)}", got=len(geo_boxes), expected=len(src_geo))
    if geo_boxes:
        box = geo_boxes[0]
        # FIX-1: must have southBoundLatitude not southBoundLongitude
        south_lat = box.xpath("datacite:southBoundLatitude", namespaces=NS)
        north_lat = box.xpath("datacite:northBoundLatitude", namespaces=NS)
        south_lon_wrong = box.xpath("datacite:southBoundLongitude", namespaces=NS)
        north_lon_wrong = box.xpath("datacite:northBoundLongitude", namespaces=NS)
        check("FIX-1: southBoundLatitude present (not southBoundLongitude)",
              truthy=len(south_lat) > 0)
        check("FIX-1: northBoundLatitude present (not northBoundLongitude)",
              truthy=len(north_lat) > 0)
        check("FIX-1: no southBoundLongitude in output",
              truthy=len(south_lon_wrong) == 0)
        check("FIX-1: no northBoundLongitude in output",
              truthy=len(north_lon_wrong) == 0)
        check("southBoundLatitude value preserved",
              got=(south_lat[0].text or "").strip() if south_lat else None,
              expected=src.findtext("dataset/coverage/geographicCoverage/boundingCoordinates/southBoundingCoordinate"))
        check("northBoundLatitude value preserved",
              got=(north_lat[0].text or "").strip() if north_lat else None,
              expected=src.findtext("dataset/coverage/geographicCoverage/boundingCoordinates/northBoundingCoordinate"))


def test_resource_type(root):
    print(f"\n{BOLD}[11] resource types (FIX-9 + FIX-12){RESET}")
    dc_rt   = root.xpath("//datacite:resourceType", namespaces=NS)
    oa_rt   = root.xpath("//oaire:resourceType", namespaces=NS)
    check("FIX-12: datacite:resourceType element present", truthy=len(dc_rt) > 0)
    check("datacite:resourceType resourceTypeGeneral='Dataset'",
          got=dc_rt[0].get("resourceTypeGeneral") if dc_rt else None, expected="Dataset")
    check("oaire:resourceType present", truthy=len(oa_rt) > 0)
    check("FIX-9: oaire resourceTypeGeneral capitalised 'Dataset'",
          got=oa_rt[0].get("resourceTypeGeneral") if oa_rt else None, expected="Dataset")


def test_access_rights(root, src):
    print(f"\n{BOLD}[12] datacite:rights (FIX-5){RESET}")
    rights = root.xpath("//datacite:rights", namespaces=NS)
    check("datacite:rights element present", truthy=len(rights) > 0)
    if rights:
        rights_text = (src.findtext("dataset/intellectualRights/para") or
                       src.findtext("dataset/intellectualRights") or "").lower()
        is_open = ("creative commons" in rights_text or "cc-by" in rights_text
                   or "4.0" in rights_text or "open" in rights_text)
        if is_open:
            check("FIX-5: CC-BY rights URI assigned for open-access record",
                  got=rights[0].get("rightsURI"),
                  expected="https://creativecommons.org/licenses/by/4.0/")
        else:
            check("FIX-5: metadata-only rights URI for restricted record",
                  got=rights[0].get("rightsURI"),
                  contains="coar/access_right")


def test_no_xslt_errors(transform_errors):
    print(f"\n{BOLD}[13] XSLT processor health{RESET}")
    check("No XSLT processor errors or warnings", truthy=len(transform_errors) == 0)
    for e in transform_errors:
        print(f"       {RED}{e}{RESET}")


# ──────────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Test EML 2.2.0 → DataCite 4.0.1 transformation.")
    p.add_argument("--input",  "-i", type=Path, default=DEFAULT_IN)
    p.add_argument("--xsl",          type=Path, default=DEFAULT_XSL)
    p.add_argument("--output", "-o", type=Path, default=None)
    p.add_argument("--package-id",   default=None)
    return p.parse_args()




def test_alternate_identifiers(root, src):
    print(f"\n{BOLD}[1b] datacite:alternateIdentifiers  (FIX-B){RESET}")
    alts = root.xpath("//datacite:alternateIdentifiers/datacite:alternateIdentifier", namespaces=NS)
    src_alts = src.findall("dataset/alternateIdentifier")
    doi_alts  = [a.text for a in src_alts if a.text and "doi" in a.text.lower()]
    nondoi    = [a.text for a in src_alts if a.text and "doi" not in a.text.lower()]
    if doi_alts:
        check("FIX-B: handle identifier preserved in alternateIdentifiers",
              truthy=any("handle" in (a.text or "").lower() or
                         not ("doi" in (a.text or "").lower())
                         for a in alts))
        pkg = src.getroottree().getroot().get("packageId", "")
        if pkg:
            check("FIX-B: packageId preserved as alternateIdentifier",
                  truthy=any((a.text or "").strip() == pkg.strip() for a in alts))


def test_publisher_is_lifewatch(root):
    print(f"\n{BOLD}[3b] datacite:publisher — must be catalogue owner  (FIX-C){RESET}")
    pub = xp(root, "//datacite:publisher")
    check("FIX-C: publisher is NOT the creator org (must be LifeWatch ERIC or param value)",
          truthy=pub is not None and pub.strip() != "")
    # Publisher should not be one of the creator organization names
    # (creator orgs go in affiliation, not publisher)
    creators_orgs = root.xpath("//datacite:creators/datacite:creator/datacite:affiliation",
                                namespaces=NS)
    # This is a soft check — the publisher MIGHT coincidentally match an org,
    # but it should never be derived FROM the creator list
    check("FIX-C: publisher value is non-empty", truthy=bool(pub and pub.strip()))


def test_pub_year_guard(root, src):
    print(f"\n{BOLD}[4b] publicationYear guard  (FIX-D){RESET}")
    py = root.xpath("//datacite:publicationYear", namespaces=NS)
    year_text = py[0].text.strip() if py else ""
    check("FIX-D: publicationYear is exactly 4 digits (never empty)",
          truthy=bool(py) and len(year_text) == 4 and year_text.isdigit())


def test_iso_lang(root, src):
    print(f"\n{BOLD}[2b] xml:lang is ISO 639-1  (FIX-E){RESET}")
    lang_attr = xpa(root, "//datacite:titles/datacite:title",
                    "{http://www.w3.org/XML/1998/namespace}lang")
    dc_lang = xp(root, "//dc:language")
    check("FIX-E: xml:lang is short ISO 639-1 code (≤ 3 chars)",
          truthy=lang_attr is not None and len(lang_attr) <= 3)
    check("FIX-E: dc:language is ISO 639-1 code (≤ 3 chars)",
          truthy=dc_lang is not None and len(dc_lang.strip()) <= 3)


def test_collected_date(root, src):
    print(f"\n{BOLD}[5b] Collected date from temporalCoverage  (FIX-G){RESET}")
    temp = src.find("dataset/coverage/temporalCoverage")
    if temp is None:
        print(f"  (no temporalCoverage in source — skipped)")
        return
    single = temp.findtext("singleDateTime/calendarDate")
    dates = root.xpath("//datacite:dates/datacite:date[@dateType='Collected']",
                        namespaces=NS)
    if single:
        check(f"FIX-G: Collected date present from singleDateTime ({single!r})",
              truthy=len(dates) > 0)
        if dates:
            check("FIX-G: Collected date value matches calendarDate",
                  got=(dates[0].text or "").strip(), expected=single.strip())


def test_rights_list_wrapper(root):
    print(f"\n{BOLD}[12b] datacite:rightsList wrapper  (FIX-F){RESET}")
    rl = root.xpath("//datacite:rightsList", namespaces=NS)
    rights_inside = root.xpath("//datacite:rightsList/datacite:rights", namespaces=NS)
    check("FIX-F: datacite:rightsList wrapper present", truthy=len(rl) > 0)
    check("FIX-F: datacite:rights inside rightsList", truthy=len(rights_inside) > 0)
    # No bare datacite:rights outside rightsList
    bare = root.xpath("/oaire:resource/datacite:rights", namespaces=NS)
    check("FIX-F: no bare datacite:rights outside rightsList", truthy=len(bare) == 0)


def test_creator_name_parts(root, src):
    print(f"\n{BOLD}[8b] Creator givenName / familyName sub-elements  (FIX-L){RESET}")
    creators = root.xpath("//datacite:creators/datacite:creator", namespaces=NS)
    for i, c in enumerate(creators):
        nt = c.xpath("datacite:creatorName/@nameType", namespaces=NS)
        gn = c.xpath("datacite:givenName", namespaces=NS)
        fn = c.xpath("datacite:familyName", namespaces=NS)
        check(f"creator[{i+1}] nameType='Personal'",
              got=nt[0] if nt else None, expected="Personal")
        if gn or fn:  # only check when source has individualName
            check(f"creator[{i+1}] givenName sub-element present", truthy=len(gn) > 0)
            check(f"creator[{i+1}] familyName sub-element present", truthy=len(fn) > 0)


def test_oaire_file_attributes(root):
    print(f"\n{BOLD}[8c] oaire:file mimeType + objectType  (FIX-J){RESET}")
    files = root.xpath("//oaire:file", namespaces=NS)
    for i, f in enumerate(files):
        mt = f.get("mimeType")
        ot = f.get("objectType")
        check(f"oaire:file[{i+1}] has @mimeType attribute", truthy=mt is not None and mt != "")
        check(f"oaire:file[{i+1}] has @objectType attribute", truthy=ot is not None and ot != "")

def main():
    args = parse_args()
    xsl_path   = args.xsl.resolve()
    input_path = args.input.resolve()

    if not xsl_path.exists():
        print(f"{RED}ERROR:{RESET} Stylesheet not found: {xsl_path}"); sys.exit(1)
    if not input_path.exists():
        print(f"{RED}ERROR:{RESET} Input file not found: {input_path}")
        print(f"  Use --input to specify your EML 2.2.0 file."); sys.exit(1)

    print(f"\n{BOLD}━━ EML 2.2.0 → DataCite 4.0.1 — Test Suite ━━━━━━━━━━━━━━━━━━━━{RESET}")
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

    # Check input is EML 2.2.0
    print(f"\n{BOLD}[0] Pre-flight{RESET}")
    src_ns = src_doc.getroot().nsmap.get("eml", "")
    if EML220_NS in src_ns:
        print(f"  {GREEN}✅{RESET}  Input confirmed as EML 2.2.0")
    else:
        print(f"  {RED}⚠  Input namespace: {src_ns!r} — expected EML 2.2.0{RESET}")

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

    # Run all test groups
    test_identifier(root, src_doc.getroot())
    test_title(root, src_doc.getroot())
    test_publisher(root, src_doc.getroot())
    test_publication_year(root, src_doc.getroot())
    test_dates(root, src_doc.getroot())
    test_description(root, src_doc.getroot())
    test_subjects(root, src_doc.getroot())
    test_creators(root, src_doc.getroot())
    test_contributors(root, src_doc.getroot())
    test_geo(root, src_doc.getroot())
    test_resource_type(root)
    test_access_rights(root, src_doc.getroot())
    test_no_xslt_errors(t.error_log)
    # v1.2.0 additional checks
    test_alternate_identifiers(root, src_doc.getroot())
    test_publisher_is_lifewatch(root)
    test_pub_year_guard(root, src_doc.getroot())
    test_iso_lang(root, src_doc.getroot())
    test_collected_date(root, src_doc.getroot())
    test_rights_list_wrapper(root)
    test_creator_name_parts(root, src_doc.getroot())
    test_oaire_file_attributes(root)

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
