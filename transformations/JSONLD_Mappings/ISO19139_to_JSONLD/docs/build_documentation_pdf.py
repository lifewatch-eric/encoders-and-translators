#!/usr/bin/env python3
"""Rebuild ISO19139_to_JsonLD_Documentation_v2.1.pdf with correct table layout.

The original PDF (produced by whatever pipeline generated it originally) had a
bug: table cells used raw strings instead of wrapped Paragraph objects, so long
cell content overlapped into the adjacent column instead of wrapping, and long
URLs overflowed past the page margin. This rebuilds the same content with every
cell wrapped in a Paragraph so reportlab wraps text within the given column
width, and column widths sized so nothing overflows the page.

To edit the documentation content (e.g. after a notebook version bump), edit
the strings below and re-run:

    pip install reportlab
    python3 build_documentation_pdf.py

Requires poppler (`brew install poppler` / `apt-get install poppler-utils`)
only if you want to preview pages as images afterwards — not for building.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ISO19139_to_JsonLD_Documentation_v2.1.pdf")

HEADER_BLUE = colors.HexColor("#1b3a5c")
ACCENT_BLUE = colors.HexColor("#2f6690")
ROW_ALT = colors.HexColor("#f5f7f9")
GRID = colors.HexColor("#c9d2d8")
CODE_BG = colors.HexColor("#f2f2f2")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=24, textColor=HEADER_BLUE, spaceAfter=6)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=13, textColor=ACCENT_BLUE, alignment=TA_CENTER, spaceAfter=10)
meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9.5, alignment=TA_CENTER, spaceAfter=4, textColor=colors.HexColor("#333333"))
whatsnew_style = ParagraphStyle("WhatsNew", parent=styles["Normal"], fontSize=9.5, alignment=TA_CENTER, spaceAfter=4)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, textColor=HEADER_BLUE, spaceBefore=14, spaceAfter=8)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5, textColor=ACCENT_BLUE, spaceBefore=10, spaceAfter=6)
body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13, spaceAfter=6)
cell = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.3, leading=10.5)
cell_head = ParagraphStyle("CellHead", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")
code_style = ParagraphStyle("Code", parent=styles["Normal"], fontName="Courier", fontSize=7.6, leading=10, backColor=CODE_BG, borderPadding=6, leftIndent=2)
bullet_style = ParagraphStyle("Bullet", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=3)
footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, spaceBefore=14)


def P(text, style=cell):
    return Paragraph(text, style)


def make_table(headers, rows, col_widths, header_style=cell_head, body_style=cell, repeat=True):
    data = [[P(h, header_style) for h in headers]] + [[P(str(c), body_style) for c in row] for row in rows]
    t = Table(data, colWidths=col_widths, repeatRows=1 if repeat else 0)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


CONTENT_WIDTH = letter[0] - 1.1 * inch * 2  # matches leftMargin+rightMargin below

doc = SimpleDocTemplate(
    OUT, pagesize=letter,
    leftMargin=1.1 * inch, rightMargin=1.1 * inch, topMargin=0.9 * inch, bottomMargin=0.9 * inch,
)

story = []

# ---------- Title page ----------
story.append(Spacer(1, 1.6 * inch))
story.append(Paragraph("ISO 19139 &rarr; JSON-LD Converter", title_style))
story.append(Paragraph("Technical Documentation — LifeWatch ERIC spec v2.1", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.2, color=HEADER_BLUE, spaceBefore=6, spaceAfter=14))
story.append(Paragraph("Version: 2.1&nbsp;&nbsp;|&nbsp;&nbsp;Date: July 14, 2026", meta_style))
story.append(Paragraph("Scope: Workflows, VREs, Services (Action / HowTo / CreativeWork)", meta_style))
story.append(Spacer(1, 8))
story.append(Paragraph(
    "<b>What changed in v2.1:</b> provider hardcoded to LifeWatch ERIC block on all record types; "
    "empty affiliation now included per sheet spec.", whatsnew_style))
story.append(PageBreak())

# ---------- 1. Overview ----------
story.append(Paragraph("1. Overview", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))
story.append(Paragraph(
    "This Google Colab notebook converts ISO 19139 XML metadata records into JSON-LD documents "
    "conforming to the LifeWatch ERIC mapping spec. Unlike the EML converter (which always produces "
    "Dataset), this notebook auto-detects the record type and maps to the appropriate schema.org type.",
    body))

story.append(Paragraph("1.1 Record type auto-detection", h2))
story.append(make_table(
    ["ISO 19139 signal", "JSON-LD @type", "Detection logic"],
    [
        ["hierarchyLevel=service + registered input/output datasets", "Action", "srv:SV_OperationMetadata or gmd:LW_Service present"],
        ["hierarchyLevel=service + Marco-Bolo keyword + no I/O", "HowTo", '"marco-bolo" in title or keywords'],
        ["hierarchyLevel=service + no Marco-Bolo + no I/O", "CreativeWork", "Default for services"],
        ['hierarchyLevel=application or "workflow"/"VRE" in title/keywords', "CreativeWork", "Workflow or VRE signals"],
        ["Default (any other)", "CreativeWork", "Fallback"],
    ],
    [2.55 * inch, 1.15 * inch, 2.2 * inch],
))
story.append(Spacer(1, 10))

story.append(Paragraph("1.2 Dependencies", h2))
story.append(make_table(
    ["Package", "Purpose"],
    [
        ["lxml", "XML parsing of ISO 19139 documents"],
        ["tabulate", "Formatted mapping-report tables"],
    ],
    [1.5 * inch, 4.4 * inch],
))
story.append(Spacer(1, 10))

story.append(Paragraph("1.3 Entry Point", h2))
story.append(Paragraph(
    "In Google Colab, run() with no arguments triggers a file-upload dialog. Record type is "
    "auto-detected. To override:", body))
story.append(Paragraph(
    "result = run(xml_path='/content/file.xml', record_type='Action')<br/>"
    "# Options: 'Workflow', 'VRE', 'Action', 'HowTo', 'CreativeWork'", code_style))

story.append(PageBreak())

# ---------- 2. What's New ----------
story.append(Paragraph("2. What's New in v2.1", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))

story.append(Paragraph("2.1 provider — hardcoded LifeWatch ERIC block", h2))
story.append(Paragraph(
    "Every record type now includes the hardcoded LifeWatch ERIC provider block, consistent with "
    "the EML converter and the LifeWatch ERIC spec:", body))
story.append(Paragraph(
    '"provider": {<br/>'
    '&nbsp;&nbsp;"@type": "Organization",<br/>'
    '&nbsp;&nbsp;"name": "e-Science and Technology European Infrastructure for<br/>'
    '&nbsp;&nbsp;Biodiversity and Ecosystem Research",<br/>'
    '&nbsp;&nbsp;"alternateName": "LifeWatch ERIC",<br/>'
    '&nbsp;&nbsp;"identifier": "https://ror.org/04c04g438",<br/>'
    '&nbsp;&nbsp;"url": "https://www.lifewatch.eu",<br/>'
    '&nbsp;&nbsp;"email": "communications@lifewatch.eu"<br/>'
    '}', code_style))

story.append(Paragraph("2.2 Empty affiliation fix", h2))
story.append(Paragraph(
    'When a contact\'s &lt;organisationName&gt; element is present but empty, the sheet spec '
    'requires "affiliation": {"@type": "Organization", "name": ""}. Previously the affiliation was '
    'silently omitted. Fixed in v2.1.', body))
story.append(Paragraph("<b>Before (v1 — missing affiliation for empty org):</b>", body))
story.append(Paragraph(
    '{"@type": "Person", "name": "Ben Hamner", "email": ""}', code_style))
story.append(Spacer(1, 6))
story.append(Paragraph("<b>After (v2.1 — affiliation always present):</b>", body))
story.append(Paragraph(
    '{"@type": "Person", "name": "Ben Hamner",<br/>'
    '&nbsp;"affiliation": {"@type": "Organization", "name": ""},<br/>'
    '&nbsp;"email": ""}', code_style))

story.append(PageBreak())

# ---------- 3. Field Mapping by Record Type ----------
story.append(Paragraph("3. Field Mapping by Record Type", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))

story.append(Paragraph("3.1 Workflow and VRE &rarr; CreativeWork", h2))
story.append(make_table(
    ["ISO 19139 Field", "JSON-LD Property", "Notes"],
    [
        ["fileIdentifier", "@id", "https://metadatacatalogue.lifewatch.eu/srv/api/records/{UUID}"],
        ["fileIdentifier", "url", "https://metadatacatalogue.lifewatch.eu/srv/eng/catalog.search#/metadata/{UUID}"],
        ["title", "name", "—"],
        ["abstract", "description", "—"],
        ["CI_Date (creation)", "dateCreated", "—"],
        ["CI_Date (publication)", "datePublished", "Empty string if element present but empty"],
        ["CI_Date (revision)", "dateModified", "Empty string if element present but empty"],
        ["MD_ProgressCode", "creativeWorkStatus", "DefinedTerm with PSO URI (see status map)"],
        ["pointOfContact", "creator", "Person/Organization — all contacts included"],
        ["useLimitation", "license", "Pass through as-is; use URL when available"],
        ["keyword", "keywords", "Plain string array"],
        ["distributionInfo/URL", "sameAs", "All URLs — string if 1, array if multiple"],
        ["(hardcoded)", "provider", "LifeWatch ERIC organisation block — always"],
    ],
    [1.55 * inch, 1.35 * inch, 3.0 * inch],
))
story.append(Spacer(1, 10))

story.append(Paragraph("3.2 Service &rarr; Action", h2))
story.append(Paragraph(
    "Used when the service has registered input/output datasets in the catalogue "
    "(srv:SV_OperationMetadata or gmd:LW_Service).", body))
story.append(make_table(
    ["ISO 19139 Field", "JSON-LD Property", "Notes"],
    [
        ["fileIdentifier", "@id + url", "Same pattern as above"],
        ["title", "name", "—"],
        ["abstract", "description", "—"],
        ["CI_Date (publication or creation)", "startTime + endTime", "Same value for both; publication date takes priority"],
        ["MD_ProgressCode", "creativeWorkStatus", "DefinedTerm with PSO URI"],
        ["pointOfContact", "agent", "agent (not creator) for Action type"],
        ["useLimitation", "(not mapped)", "License not mapped for Action per spec"],
        ["keyword", "(not mapped)", "Keywords not mapped for Action per spec"],
        ["distributionInfo/URL", "sameAs", "Last URL only (the runnable workflow/NaaVRE link)"],
        ["(hardcoded)", "provider", "LifeWatch ERIC organisation block — always"],
    ],
    [1.55 * inch, 1.35 * inch, 3.0 * inch],
))

story.append(PageBreak())

story.append(Paragraph("3.3 Service &rarr; HowTo", h2))
story.append(Paragraph("Used when the service is part of Marco-Bolo and has no registered I/O.", body))
story.append(make_table(
    ["ISO 19139 Field", "JSON-LD Property", "Notes"],
    [
        ["fileIdentifier", "@id + url", "—"],
        ["title", "name", "—"],
        ["abstract", "description", "—"],
        ["CI_Date (creation/publication/revision)", "dateCreated / datePublished / dateModified", "—"],
        ["MD_ProgressCode", "creativeWorkStatus", "DefinedTerm with PSO URI"],
        ["pointOfContact", "creator", "Person/Organization — all contacts"],
        ["useLimitation", "license", "Use URL when available"],
        ["keyword", "keywords", "Plain string array"],
        ["distributionInfo/URL", "sameAs", "All URLs"],
        ["(hardcoded)", "provider", "LifeWatch ERIC organisation block — always"],
    ],
    [1.55 * inch, 1.35 * inch, 3.0 * inch],
))
story.append(Spacer(1, 10))

story.append(Paragraph("3.4 Service &rarr; CreativeWork", h2))
story.append(Paragraph(
    "Used when the service has no registered I/O and is not part of Marco-Bolo. Same field mapping "
    "as HowTo — only @type differs.", body))
story.append(Spacer(1, 6))

story.append(Paragraph("3.5 MD_ProgressCode &rarr; creativeWorkStatus mapping", h2))
story.append(make_table(
    ["ISO code", "name", "PSO URI"],
    [
        ["completed", "Published", "http://purl.org/spar/pso/published"],
        ["onGoing", "Published", "http://purl.org/spar/pso/published"],
        ["underDevelopment", "Draft", "http://purl.org/spar/pso/draft"],
        ["historicalArchive", "Archived", "http://purl.org/spar/pso/archived"],
        ["obsolete", "Archived", "http://purl.org/spar/pso/archived"],
    ],
    [1.5 * inch, 1.2 * inch, 3.2 * inch],
))

story.append(PageBreak())

# ---------- 4. Complete Mapping Summary ----------
story.append(Paragraph("4. Complete Mapping Summary", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))
story.append(make_table(
    ["ISO 19139 Field", "Status", "Workflow / VRE", "Action", "HowTo / CreativeWork"],
    [
        ["fileIdentifier", "OK", "@id + url", "@id + url", "@id + url"],
        ["title", "OK", "name", "name", "name"],
        ["abstract", "OK", "description", "description", "description"],
        ["CI_Date creation", "OK", "dateCreated", "—", "dateCreated"],
        ["CI_Date publication", "OK", "datePublished", "startTime + endTime", "datePublished"],
        ["CI_Date revision", "OK", "dateModified", "—", "dateModified"],
        ["MD_ProgressCode", "OK", "creativeWorkStatus", "creativeWorkStatus", "creativeWorkStatus"],
        ["pointOfContact", "OK", "creator", "agent", "creator"],
        ["useLimitation", "OK / NOT MAPPED", "license", "not mapped", "license"],
        ["keyword", "OK / NOT MAPPED", "keywords[]", "not mapped", "keywords[]"],
        ["distributionInfo/URL", "OK", "sameAs (all URLs)", "sameAs (last URL)", "sameAs (all URLs)"],
        ["provider (LifeWatch ERIC)", "OK", "hardcoded block", "hardcoded block", "hardcoded block"],
    ],
    [1.35 * inch, 0.85 * inch, 1.3 * inch, 1.2 * inch, 1.5 * inch],
))
story.append(Spacer(1, 14))

# ---------- 5. Architecture ----------
story.append(Paragraph("5. Architecture", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))
story.append(make_table(
    ["Component", "Role"],
    [
        ["Constants / NS", "JSONLD_CONTEXT, CATALOGUE_HOST, STATUS_MAP, UUID_RE, NS namespaces"],
        ["_xp / _text / _texts / _attr", "XPath helper utilities"],
        ["parse_contact()", "Build Person/Organization node from CI_ResponsibleParty"],
        ["get_dates()", "Extract creation/publication/revision dates from CI_Date elements"],
        ["get_distribution_urls()", "Collect all online URLs from distributionInfo"],
        ["detect_record_type()", "Auto-detect Action/HowTo/CreativeWork from hierarchyLevel + keywords"],
        ["ISO19139toJsonLD class", "_map_* methods + convert() + save() + print_loss_report()"],
        ["run()", "Top-level orchestrator (upload &rarr; convert &rarr; save &rarr; preview &rarr; download)"],
    ],
    [1.9 * inch, 3.9 * inch],
))
story.append(Spacer(1, 10))

story.append(Paragraph("5.1 Conversion pipeline", h2))
pipeline_items = [
    "<b>_map_id()</b> — Sets @id and url from fileIdentifier UUID",
    "<b>_map_basic()</b> — Maps title &rarr; name, abstract &rarr; description",
    "<b>_map_dates()</b> — Maps dates differently per type: dateCreated/Published/Modified or startTime+endTime",
    "<b>_map_status()</b> — Maps MD_ProgressCode &rarr; creativeWorkStatus DefinedTerm with PSO URI",
    "<b>_map_contacts()</b> — Maps pointOfContact &rarr; creator or agent; injects LifeWatch ERIC provider",
    "<b>_map_license()</b> — Maps useLimitation &rarr; license (skipped for Action)",
    "<b>_map_keywords()</b> — Maps keywords as plain strings (skipped for Action)",
    "<b>_map_distribution()</b> — Maps distributionInfo URLs &rarr; sameAs (last URL only for Action)",
]
for item in pipeline_items:
    story.append(Paragraph(item, bullet_style, bulletText="•"))

story.append(PageBreak())

# ---------- 6. Usage Guide ----------
story.append(Paragraph("6. Usage Guide", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))

story.append(Paragraph("6.1 Google Colab", h2))
story.append(Paragraph(
    "Runtime &rarr; Restart runtime &rarr; Runtime &rarr; Run all, then upload your ISO 19139 XML. "
    "Record type is auto-detected from the XML content.", body))

story.append(Paragraph("6.2 Programmatic usage", h2))
story.append(Paragraph(
    "# Auto-detect (recommended)<br/>"
    "result = run(xml_path='/path/to/record.xml')<br/><br/>"
    "# Override record type<br/>"
    "result = run(xml_path='/path/to/record.xml', record_type='Action')<br/><br/>"
    "# Direct class usage<br/>"
    "conv = ISO19139toJsonLD('/path/to/record.xml')<br/>"
    "doc = conv.convert(record_type='HowTo')<br/>"
    "conv.save('record.jsonld')<br/>"
    "conv.print_loss_report()", code_style))

story.append(Paragraph("6.3 Mapping report status codes", h2))
story.append(make_table(
    ["Status", "Meaning"],
    [
        ["OK", "Field successfully mapped"],
        ["PARTIAL", "Field attempted but only partially handled"],
        ["LOST", "Field absent in the source XML"],
    ],
    [1.3 * inch, 4.6 * inch],
))
story.append(Spacer(1, 12))

# ---------- 7. Version History ----------
story.append(Paragraph("7. Version History", h1))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceAfter=8))
story.append(make_table(
    ["Version", "Change"],
    [
        ["v2.1", "provider hardcoded to LifeWatch ERIC block on all record types; empty affiliation fix."],
        ["v2.0", "Auto-detection of record type added (Workflow/VRE/Action/HowTo/CreativeWork)."],
        ["v1.0", "Initial implementation covering Workflow, VRE, Action, HowTo, CreativeWork."],
    ],
    [0.9 * inch, 5.0 * inch],
))

story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=0.5, color=GRID, spaceAfter=6))
story.append(Paragraph(
    "Generated from ISO19139_to_JsonLD_v2.1.ipynb — LifeWatch ERIC spec v2.1. "
    "External validation: https://validator.schema.org/", footer_style))

doc.build(story)
print("Built:", OUT)
