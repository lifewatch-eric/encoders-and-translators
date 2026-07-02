# EML 2.2.0 → DataCite 4.0.1 (OpenAIRE)

Transforms an **EML 2.2.0** metadata record into an **OpenAIRE / DataCite 4.0.1** resource description (`oaire:resource`), enabling dataset metadata published on the LifeWatch ERIC Metadata Catalogue to be exposed via the OAI-PMH → OpenAIRE → EOSC portal onboarding pipeline.

---

## Overview

| Property | Value |
|---|---|
| Source format | EML 2.2.0 (`https://eml.ecoinformatics.org/eml-2.2.0`) |
| Target format | OpenAIRE Literature & Data Guidelines 4.0 + DataCite 4.0.1 |
| Output root element | `oaire:resource` |
| XSLT version | 1.0 |
| Stylesheet | `xslt/main.xsl` |
| Version | 1.3.0 |
| Status | ✅ Stable  all tests passing on both bundled samples |
| Original author | LifeWatch ERIC Service Centre (service.centre@lifewatch.eu) , LifeWatch ERIC |
| Revised by | LifeWatch ERIC Service Centre |
| License | CC-BY-4.0 |

---

## Purpose

This stylesheet was developed by LifeWatch ERIC to expose dataset metadata records published on the [LifeWatch ERIC Metadata Catalogue](https://metadatacatalogue.lifewatch.eu) via OAI-PMH, allowing OpenAIRE to automatically harvest them and make resources visible in OpenAIRE Explore and the EOSC Portal.

```
EML 2.2.0 metadata
       │
       ▼  xslt/main.xsl
oaire:resource (DataCite 4.0.1)
       │
       ▼  OAI-PMH harvest
OpenAIRE → EOSC Portal
```

> ⚠ This stylesheet must be considered **unstable** and may be updated at any time based on revisions to the LifeWatch ERIC Application Profile and related OpenAIRE framework work.

---

## File Structure

```
EML220_to_DataCite401/
├── xslt/
│   └── main.xsl                              ← transformation stylesheet (v1.3.0)
├── examples/
│   ├── input/
│   │   ├── lesina-phytoplankton-eml220.xml   ← EML 2.2.0 sample input
│   │   └── 8_Macrozoobenthos_data_collected_in_the_Acquatina_lagoon,_Apulia,_Italy.xml
│   └── output/
│       ├── lesina-phytoplankton-datacite401.xml
│       └── 8_Macrozoobenthos_data_collected_in_the_Acquatina_lagoon,_Apulia,_Italy_datacite401.xml
├── docs/
│   ├── mapping-notes.md                      ← field level mapping reference
│   └── transformation-diagram.svg           ← visual flow diagram (open in browser)
├── run.py                                    ← one command transform + test runner
├── test_transformation.py                    ← automated test suite
└── README.md                                 ← this file
```

---

## Transformation Diagram

Open `docs/transformation-diagram.svg` in any browser to see the visual flow of the transformation steps. Note: the diagram was authored against an earlier stylesheet revision  refer to the sections below for the current, authoritative field-by-field behaviour.

---

## Transformation Steps

### ① `datacite:identifier` + `datacite:alternateIdentifiers`

The stylesheet **prefers a DOI** `alternateIdentifier` when present; otherwise builds a catalogue URL.

| Condition | `identifierType` | Value |
|---|---|---|
| DOI `alternateIdentifier` exists | `DOI` | The DOI text (first match, case-insensitive) |
| No DOI, but a handle/UUID/URL identifier exists | `URL` | `$catalogue-url` + that identifier |
| Neither present | `URL` | `$catalogue-url` + `packageId` |

When a DOI **is** used as the primary identifier, the non-DOI identifier (handle/UUID/URL) and `packageId` are **not discarded**  they're preserved in `datacite:alternateIdentifiers` (`Handle`, `URL`, or `PackageID` typed).

---

### ② `datacite:titles` / `datacite:title`

| EML source | DataCite output | Notes |
|---|---|---|
| `dataset/title` | `datacite:title` | `normalize-space()` applied |
| `dataset/language` | `xml:lang` (ISO 639-1) | Omitted when language is empty |

---

### ③ `datacite:publisher`

Always set to the `$default-publisher` parameter (default: `"LifeWatch ERIC"`). Per the DataCite definition, publisher is the entity that *holds/archives/distributes* the resource  the catalogue owner, not the dataset's creator organisation. A creator's org still appears, but under `datacite:affiliation` on that creator, never as `datacite:publisher`.

---

### ④ `datacite:publicationYear`

Extracted as `substring(normalize-space(./pubDate), 1, 4)`. Guarded: if `pubDate` is empty or too short to yield 4 digits, no (invalid, empty) `publicationYear` element is emitted at all.

---

### ⑤ `datacite:dates`

| `@dateType` | EML source |
|---|---|
| `Issued` | `dataset/pubDate` |
| `Collected` | `coverage/temporalCoverage/singleDateTime/calendarDate` |
| `Collected` | `coverage/temporalCoverage/rangeOfDates` → emitted as an ISO 8601 interval, `start/end` |

---

### ⑥ `dc:language`

`dataset/language` is normalised to an ISO 639-1 two-letter code (e.g. `"English"` → `en`) via the `iso-lang` named template, covering en/it/fr/de/es/pt/nl/el; unrecognised values pass through lower-cased.

---

### ⑦ `datacite:descriptions` / `datacite:description`

EML 2.2.0 wraps abstract text in `<para>` children. The stylesheet reads them:

```
abstract/para[1] + " " + abstract/para[N]  →  datacite:description[@descriptionType="Abstract"]
```

Fallback to `normalize-space(./abstract)` when no `<para>` children exist.

---

### ⑧ `datacite:sizes` and `datacite:formats`

- `datacite:sizes` ← `dataTable/physical/size` (value + `@unit` when present).
- `datacite:formats` ← detected from the delimited-text `fieldDelimiter` and/or the `objectName` file extension (CSV, TSV, XML, JSON, XLSX/XLS; otherwise `text/plain`).

---

### ⑨ `datacite:subjects`

Each keyword becomes a `datacite:subject`.

| `keywordThesaurus` | `@subjectScheme` |
|---|---|
| Present and not `"none"` | Set to the thesaurus name |
| Absent or `"none"` | **`"NA"`**  the attribute is always present, never omitted |

---

### ⑩ File Locations (`oaire:file`)

Two URL sources, each iterated **exactly once**:

| Source | EML path |
|---|---|
| **A** — direct | `dataset/distribution/online/url` |
| **B** — GBIF physical | `additionalMetadata/metadata/gbif/physical/distribution/online/url` |

- Contains "doi" (case-insensitive) → `datacite:alternateIdentifier[@alternateIdentifierType='DOI']`
- Otherwise → `oaire:file`, now carrying `@mimeType` (detected the same way as `datacite:formats`) and `@objectType="fulltext"`.

---

### ⑪ `datacite:creators`

For each `dataset/creator`:

| Element | Source | Condition |
|---|---|---|
| `datacite:creatorName[@nameType="Personal"]` | `"Surname, GivenName"` | When `individualName` present |
| `datacite:creatorName` | `organizationName` | Fallback when no `individualName` |
| `datacite:givenName` / `datacite:familyName` | `individualName/givenName` / `surName` | Only when non-empty |
| `datacite:affiliation` | `organizationName` | Only when non-empty |
| `datacite:nameIdentifier[@nameIdentifierScheme='ORCID']` | `userId` | **Only when `userId` is non-empty** — never emitted empty |

---

### ⑫ `datacite:contributors`

| EML element | `@contributorType` |
|---|---|
| `dataset/contact` | `ContactPerson` |
| `dataset/metadataProvider` | `DataManager` |

Same `nameType="Personal"`, affiliation, and ORCID-suppression handling as creators.

---

### ⑬ `datacite:fundingReferences`

`project/funding` (or `project/funding/para`) → `datacite:fundingReference/datacite:funderName`. Omitted entirely when no funding text is present.

---

### ⑭ `datacite:geoLocations`

| DataCite element | EML source |
|---|---|
| `westBoundLongitude` / `eastBoundLongitude` | `westBoundingCoordinate` / `eastBoundingCoordinate` |
| `southBoundLatitude` | `southBoundingCoordinate` |
| `northBoundLatitude` | `northBoundingCoordinate` |

`geoLocationPlace` suppressed when `geographicDescription` is empty. `geoLocationBox` suppressed when `boundingCoordinates` is absent. Only `geoLocationBox` is mapped  `geoLocationPoint` is not (see Known Limitations).

---

### ⑮ Resource Types

**Three** elements are always emitted:

```xml
<datacite:resourceType resourceTypeGeneral="Dataset">Dataset</datacite:resourceType>
<oaire:resourceType resourceTypeGeneral="dataset"
    uri="http://purl.org/coar/resource_type/c_ddb1">dataset</oaire:resourceType>
<oaire:resourceType resourceTypeGeneral="Dataset"
    uri="http://purl.org/coar/resource_type/c_ddb1">dataset</oaire:resourceType>
```

The legacy lowercase `oaire:resourceType resourceTypeGeneral="dataset"` is kept alongside a newer capitalised form, per the 2026-07 OpenAIRE guidelines review. This duplication is intentional (see the review notes) but worth re-confirming with OpenAIRE validators if it ever causes a harvest warning.

---

### ⑯ `datacite:rightsList` / `datacite:rights`

Rights detection is performed on `intellectualRights/para` text (fallback to `intellectualRights` direct text):

| Condition (case-insensitive) | Output |
|---|---|
| `"creative commons"`, `"cc-by"`, `"4.0"`, or `"open access"` | **Two** entries: the COAR open-access URI (`c_abf2`) **and** a CC-BY-4.0 / SPDX entry |
| None of the above | One entry: COAR "metadata only access" (`c_14cb`) |

Both entries live inside a single `datacite:rightsList` wrapper (required by DataCite 4.x  no bare `datacite:rights` outside it).

---

## Bug Fix / Change Log

### v1.1.0  original correctness fixes

| # | Severity | Bug | Fix |
|---|---|---|---|
| FIX-1 | 🔴 Critical | `northBoundLongitude` / `southBoundLongitude` (wrong element names) | → `northBoundLatitude` / `southBoundLatitude` |
| FIX-2 | 🔴 Critical | Double-nested `for-each` → duplicate file/DOI entries | Removed inner loop |
| FIX-3 | 🔴 Critical | Empty `<datacite:nameIdentifier>` always emitted | Wrapped with `xsl:if` on `userId` |
| FIX-4 | 🟠 Major | `select="./abstract"` returns empty | Changed to `./abstract/para` |
| FIX-5 | 🟠 Major | Rights tested on whole `<dataset>` not `intellectualRights` | Fixed to `./intellectualRights/para` |
| FIX-6 | 🟠 Major | Identifier always used first `alternateIdentifier` | Now prefers DOI |
| FIX-7 | 🟠 Major | `datacite:title` missing `xml:lang` | Added from `./language` |
| FIX-8 | 🟡 Minor | Used `dc:description` instead of `datacite:description` | Replaced with correct element |
| FIX-9 | 🟡 Minor | `resourceTypeGeneral="dataset"` (lowercase) | → `"Dataset"` |
| FIX-10 | 🟡 Minor | `datacite:publisher` missing | Added |
| FIX-11 | 🟡 Minor | `datacite:publicationYear` missing | Added |
| FIX-12 | 🟡 Minor | `datacite:resourceType` missing | Added |

### v1.2.0 (2026-04-15)  12 further fixes

| # | Change |
|---|---|
| FIX-A | Explicit DOI selection: first `alternateIdentifier` containing "doi", case-insensitive, no last-wins risk |
| FIX-B | Non-DOI identifiers (handle, UUID) preserved in `datacite:alternateIdentifiers` instead of silently dropped |
| FIX-C | Publisher is always `$default-publisher` (LifeWatch ERIC)  creator org goes in `affiliation`, never in `publisher` |
| FIX-D | `publicationYear` guard: empty `pubDate` no longer emits an invalid empty element |
| FIX-E | `xml:lang` / `dc:language` normalised to ISO 639-1 (`en`, not `English`) |
| FIX-F | `datacite:rightsList` wrapper added (required by DataCite 4.x) |
| FIX-G | Temporal coverage mapped to `datacite:date[@dateType='Collected']`  both `singleDateTime` and `rangeOfDates` |
| FIX-H | `datacite:sizes` from `dataTable/physical/size` |
| FIX-I | `datacite:formats` detected from `fieldDelimiter` / `objectName` |
| FIX-J | `oaire:file` now carries `@mimeType` and `@objectType` |
| FIX-K | `datacite:fundingReferences` from `project/funding` |
| FIX-L | `datacite:creatorName` / `contributorName` carry `@nameType="Personal"`; `givenName` / `familyName` sub-elements added |

### v1.3.0 (2026-07-02) — OpenAIRE guidelines review

| # | Change | Source |
|---|---|---|
| FIX-M | `datacite:subject` carries `subjectScheme="NA"` when no `keywordThesaurus`, instead of omitting the attribute | OpenAIRE guidelines review  `field_subject` |
| FIX-N | `oaire:resourceType` now emitted **twice**: legacy lowercase `resourceTypeGeneral="dataset"` kept for backward compatibility, alongside a new capitalised `resourceTypeGeneral="Dataset"` form | OpenAIRE guidelines review |
| FIX-O | `datacite:rightsList` includes **both** the original COAR access-right entry (`c_abf2`, "open access") and the new CC-BY-4.0 / SPDX entry for open-access records  one no longer replaces the other | OpenAIRE guidelines review |

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `$default-publisher` | `LifeWatch ERIC` | Publisher for every record (catalogue owner, not the creator org) |
| `$catalogue-url` | `https://metadatacatalogue.lifewatch.eu/srv/eng/catalog.search#/metadata/` | Base URL for catalogue record links when no DOI is present |

---

## Quick Start

```bash
pip install lxml
cd transformations/EML220_to_DataCite401

# Drop your EML 2.2.0 file into examples/input/ then:
python3 run.py

# Output appears in examples/output/ automatically.
# If you delete the output and run again — it regenerates.
python3 run.py --force    # re-run even when output exists
```

### run.py Flags

```bash
python3 run.py                                    # all new inputs
python3 run.py --force                            # re-run all
python3 run.py --input examples/input/file.xml   # single file
python3 run.py --output /path/to/result.xml       # custom output path
python3 run.py --publisher "My Institution"       # override publisher
python3 run.py --package-id my.new.id             # override packageId
python3 run.py --no-tests                         # transform only
python3 run.py --open-folder                      # open output/ in Finder
python3 run.py --quiet                            # summary only
```

### test_transformation.py

```bash
python3 test_transformation.py                               # bundled sample
python3 test_transformation.py --input your-file.xml        # your file
python3 test_transformation.py --input f.xml --output r.xml # test + save
```

---

## Known Limitations

| EML element | DataCite target | Status |
|---|---|---|
| `licensed/url` | `rights/@rightsURI` | Not mapped  rights are inferred from `intellectualRights` text only |
| `methods` | `description[@descriptionType='Methods']` | Not mapped |
| `geographicCoverage` point | `geoLocationPoint` | Only `geoLocationBox` mapped |
| Multiple titles | `datacite:titles` with several `datacite:title` (different languages) | Only a single title is emitted; the LifeWatch ERIC Application Profile does not currently carry multi-language titles, so this hasn't been needed in practice |

---

## See Also

- [DataCite Metadata Schema 4.x](https://schema.datacite.org/meta/kernel-4/)
- [OpenAIRE Guidelines v4](https://openaire-guidelines-for-literature-repository-managers.readthedocs.io/)
- [EML 2.2.0 specification](https://eml.ecoinformatics.org/)
- [Transformation diagram](docs/transformation-diagram.svg)
- [Field mapping reference](docs/mapping-notes.md)
- [Repository README](../../README.md)
