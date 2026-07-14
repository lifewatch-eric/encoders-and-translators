# ISO 19139 → DataCite 4.0.1 (OpenAIRE)

Transforms an **ISO 19139** (`gmd:MD_Metadata`) record describing a LifeWatch
**Workflow** or **Virtual Research Environment (VRE)** into an **OpenAIRE / DataCite
4.0.1** resource description (`oaire:resource`), for the **Harvesting with OpenAIRE**
program.

---

## Overview

| Property | Value |
|---|---|
| Source format | ISO 19139 (`http://www.isotc211.org/2005/gmd`) |
| Target format | OpenAIRE Guidelines v4 / DataCite 4.0.1 (`oaire:resource`, XML) |
| Resource types | `Workflow`, `VRE` (selected via `$resource-type`) |
| XSLT version | 1.0 |
| Stylesheet | `xslt/main.xsl` |
| Version | 1.0.0 |
| Status | 🚧 In progress — mapping complete, core fields implemented; creation date, revision date, status and non-DOI distribution links are intentionally unmapped (see [Known Limitations](docs/mapping-notes.md#known-limitations)) |
| Program | Harvesting with OpenAIRE |
| Author | LifeWatch ERIC Service Centre |
| License | MIT |

---

## Purpose

LifeWatch registers two kinds of interactive resources as ISO 19139 records:
**Workflows** (created via `my.lifewatch.eu/workflow`) and **Virtual Research
Environments** (VREs / vLabs, e.g. via NaaVRE). OpenAIRE harvesting expects both in
the same `oaire:resource` / DataCite shape already used for LifeWatch datasets by the
sibling [`EML220_to_DataCite401`](../EML220_to_DataCite401) transformation. This
stylesheet maps the fields the source sheet (`ISO19139 - to - DataCite4.1.xlsx`)
identifies as derivable from ISO 19139 directly — title, abstract, publication date,
responsible parties, license, keywords, and a DOI when present — into that same
vocabulary, switching only the fixed `resourceType` pair based on `$resource-type`.

```
ISO 19139 (gmd:MD_Metadata, Workflow or VRE)
       │
       ▼  xslt/main.xsl  ($resource-type = Workflow | VRE)
oaire:resource (OpenAIRE / DataCite 4.0.1 XML)
       │
       ▼  harvested by OpenAIRE
EOSC / OpenAIRE Explore
```

---

## File Structure

```
ISO19139_to_DataCite401/
├── xslt/
│   └── main.xsl                                  ← transformation stylesheet (v1.0.0)
├── examples/
│   ├── input/
│   │   ├── crustaceans-workflow-iso19139.xml     ← Workflow sample (no DOI — tests URL fallback)
│   │   └── biodiversity-vre-iso19139.xml         ← VRE sample (DOI + 2 responsible parties)
│   └── output/
│       ├── crustaceans-workflow-datacite401.xml
│       └── biodiversity-vre-datacite401.xml
├── docs/
│   ├── mapping-notes.md                          ← field-level mapping reference
│   └── transformation-diagram.svg                ← visual flow diagram (open in browser)
├── run.py                                         ← one-command transform + test runner
├── test_transformation.py                         ← automated test suite
└── README.md                                      ← this file
```

---

## Transformation Diagram

Open `docs/transformation-diagram.svg` in any browser to see the visual flow of the
transformation steps, or read the field-by-field breakdown in `docs/mapping-notes.md`.

---

## Mapping Summary

| `oaire:resource` field | ISO 19139 source |
|---|---|
| `datacite:identifier` | DOI-shaped `distributionInfo` online resource, else `$catalogue-base-url` + `fileIdentifier` |
| `datacite:alternateIdentifiers` | `fileIdentifier` → `PackageID` |
| `datacite:titles/title` | `citation/title` |
| `datacite:publisher` | fixed `"LifeWatch ERIC"` |
| `datacite:publicationYear`, `datacite:dates[Issued]` | citation date typed `publication` |
| `datacite:descriptions[Abstract]` | `MD_DataIdentification/abstract` |
| `datacite:subjects` | `descriptiveKeywords/MD_Keywords/keyword` |
| `datacite:creators` / `datacite:contributors` | every `CI_ResponsibleParty`, routed by `gmd:role` through the 11-role table |
| `datacite:rightsList` | `resourceConstraints/MD_LegalConstraints/useLimitation` |
| `resourceType` pair | fixed per `$resource-type` (`Workflow` \| `VRE`) |

See [docs/mapping-notes.md](docs/mapping-notes.md) for the full field-level reference,
the complete role-routing table, and every field left unmapped and why.

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `$resource-type` | `Workflow` | Selects the fixed `resourceType` pair. Values: `Workflow` \| `VRE` |
| `$default-publisher` | `LifeWatch ERIC` | Value written to `datacite:publisher` |
| `$catalogue-base-url` | `https://metadatacatalogue.lifewatch.eu/srv/api/records/` | Prefixed to `fileIdentifier` for the DOI-less identifier fallback |

---

## Quick Start

```bash
pip install lxml
cd transformations/ISO19139_to_DataCite401

# Drop your ISO 19139 record into examples/input/ then:
python3 run.py --resource-type Workflow
python3 run.py --resource-type VRE

# Output appears in examples/output/ automatically.
python3 run.py --force                       # re-run even when output exists
```

### run.py Flags

```bash
python3 run.py                                     # all new inputs, resource-type=Workflow
python3 run.py --resource-type VRE                  # switch the fixed resourceType pair
python3 run.py --force                             # re-run all
python3 run.py --input examples/input/file.xml     # single file
python3 run.py --output /path/to/result.xml        # custom output path
python3 run.py --publisher "My Org"
python3 run.py --no-tests                          # transform only
python3 run.py --open-folder                       # open output/ in Finder
python3 run.py --quiet                             # summary only
```

### test_transformation.py

```bash
python3 test_transformation.py                                          # bundled sample, Workflow
python3 test_transformation.py --input your-file.xml --resource-type VRE
python3 test_transformation.py --input f.xml --output r.xml             # test + save
```

---

## Known Limitations

See the [Known Limitations](docs/mapping-notes.md#known-limitations) section of the
mapping notes — notably: `creation date` / `revision date` / `status` are marked "Not
mapped" in the source sheet and omitted; the `originator` role (used in the VRE
worked example) isn't in the sheet's own routing table and falls back to
`contributorType="Other"`; `rightsList` text is always the literal `"open access"`
per the sheet's worked example, even for non-open licenses; and non-DOI distribution
links are dropped since the source sheet leaves that case as an open question.

---

## See Also

- [OpenAIRE Guidelines for Literature Repository Managers v4](https://openaire-guidelines-for-literature-repository-managers.readthedocs.io/)
- [DataCite Metadata Schema 4.0.1](https://schema.datacite.org/meta/kernel-4.0.1/)
- [ISO 19139 schema (OGC)](http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd)
- [Field mapping reference](docs/mapping-notes.md)
- [Sibling: EML220_to_DataCite401](../EML220_to_DataCite401)
- [Repository README](../../README.md)
