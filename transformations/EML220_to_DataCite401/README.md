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
| Version | 1.1.0 |
| Status | ✅ Stable — 40/40 tests passing |
| Original author | Houda Ben Salah (houda.bensalah@lifewatch.eu), LifeWatch ERIC |
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
│   └── main.xsl                              ← transformation stylesheet (v1.1.0)
├── examples/
│   ├── input/
│   │   └── lesina-phytoplankton-eml220.xml   ← EML 2.2.0 sample input
│   └── output/
│       └── lesina-phytoplankton-datacite401.xml  ← DataCite 4.0.1 output
├── docs/
│   ├── mapping-notes.md                      ← field-level mapping reference
│   └── transformation-diagram.svg           ← visual flow diagram (open in browser)
├── run.py                                    ← one-command transform + test runner
├── test_transformation.py                    ← 40-assertion test suite
└── README.md                                 ← this file
```

---

## Transformation Diagram

Open `docs/transformation-diagram.svg` in any browser to see the full visual flow of all 14 transformation operations, with decision branches and bug-fix annotations on each step.

---

## All 14 Transformation Steps

### ① `datacite:identifier`

The stylesheet **prefers a DOI** `alternateIdentifier` when present; otherwise builds a catalogue URL.

| Condition | `identifierType` | Value |
|---|---|---|
| DOI `alternateIdentifier` exists | `DOI` | Full DOI URI (e.g. `https://doi.org/10.48372/...`) |
| No DOI present | `URL` | `$catalogue-url` + non-DOI identifier or `packageId` |

DOI detection is case-insensitive via `translate()`. The `$catalogue-url` parameter defaults to `https://metadatacatalogue.lifewatch.eu/srv/eng/catalog.search#/metadata/`.

---

### ② `datacite:titles` / `datacite:title`

| EML source | DataCite output | Notes |
|---|---|---|
| `dataset/title` | `datacite:title` | `normalize-space()` applied |
| `dataset/language` | `xml:lang` attribute | Omitted when language is empty |

---

### ③ `datacite:publisher`

Populated in order of preference:
1. `creator[1]/organizationName`
2. `$default-publisher` parameter (default: `"LifeWatch ERIC"`)

---

### ④ `datacite:publicationYear`

Extracted as `substring(normalize-space(./pubDate), 1, 4)` — works for both `YYYY` and `YYYY-MM-DD`.

---

### ⑤ `datacite:dates`

Full `pubDate` preserved as `datacite:date[@dateType="Issued"]`.

---

### ⑥ `dc:language`

`dataset/language` → `dc:language` (free text, no ISO 639-1 normalisation).

---

### ⑦ `datacite:descriptions` / `datacite:description`

EML 2.2.0 wraps abstract text in `<para>` children. The stylesheet reads them:

```
abstract/para[1] + " " + abstract/para[N]  →  description[@descriptionType="Abstract"]
```

Fallback to `normalize-space(./abstract)` when no `<para>` children exist.

> **Note:** The original v1.0 used `<dc:description>` and `select="./abstract"` — both wrong. Fixed in v1.1.0.

---

### ⑧ `datacite:subjects`

Each keyword becomes a `datacite:subject`. `keywordThesaurus` becomes `@subjectScheme` when non-empty and not equal to `"none"` (case-insensitive).

---

### ⑨ File Locations

Two URL sources, each iterated **exactly once**:

| Source | EML path |
|---|---|
| **A** — direct | `dataset/distribution/online/url` |
| **B** — GBIF physical | `additionalMetadata/metadata/gbif/physical/distribution/online/url` |

- Contains "doi" (case-insensitive) → `datacite:alternateIdentifier[@alternateIdentifierType='DOI']`
- Otherwise → `oaire:file`

> **Note:** The original v1.0 nested Source B's loop inside itself — every URL was emitted twice. Fixed by removing the inner loop.

---

### ⑩ `datacite:creators`

For each `dataset/creator`:

| Element | Source | Condition |
|---|---|---|
| `datacite:creatorName` | `"Surname, GivenName"` | When `individualName` present |
| `datacite:creatorName` | `organizationName` | Fallback when no `individualName` |
| `datacite:affiliation` | `organizationName` | Only when non-empty |
| `datacite:nameIdentifier[@nameIdentifierScheme='ORCID']` | `userId` | **Only when `userId` is non-empty** |

> **Note:** The original v1.0 always emitted an empty `<datacite:nameIdentifier>` when `userId` was absent, producing invalid XML. Fixed with `xsl:if`.

---

### ⑪ `datacite:contributors`

| EML element | `@contributorType` |
|---|---|
| `dataset/contact` | `ContactPerson` |
| `dataset/metadataProvider` | `DataManager` |

Same ORCID suppression guard as creators.

---

### ⑫ `datacite:geoLocations`

| DataCite element | EML source | v1.0 (wrong) | v1.1.0 (correct) |
|---|---|---|---|
| `westBoundLongitude` | `westBoundingCoordinate` | ✅ | ✅ |
| `eastBoundLongitude` | `eastBoundingCoordinate` | ✅ | ✅ |
| **`southBoundLatitude`** | `southBoundingCoordinate` | ❌ `southBoundLongitude` | ✅ |
| **`northBoundLatitude`** | `northBoundingCoordinate` | ❌ `northBoundLongitude` | ✅ |

`geoLocationPlace` suppressed when `geographicDescription` is empty. `geoLocationBox` suppressed when `boundingCoordinates` is absent.

---

### ⑬ Resource Types

Both elements always emitted:

```xml
<datacite:resourceType resourceTypeGeneral="Dataset">Dataset</datacite:resourceType>
<oaire:resourceType resourceTypeGeneral="Dataset"
    uri="http://purl.org/coar/resource_type/c_ddb1">dataset</oaire:resourceType>
```

> **Note:** The original v1.0 had lowercase `"dataset"` (wrong per DataCite 4.x spec) and was missing `datacite:resourceType` entirely.

---

### ⑭ `datacite:rights`

Rights detection is performed on `intellectualRights/para` text (fallback to `intellectualRights` direct text):

| Condition (case-insensitive) | Output |
|---|---|
| `"creative commons"` | CC-BY-4.0 open access |
| `"cc-by"` | CC-BY-4.0 open access |
| `"4.0"` | CC-BY-4.0 open access |
| `"open access"` | CC-BY-4.0 open access |
| None of the above | metadata only access |

> **Note:** The original v1.0 tested `contains(., '4.0')` on `.` bound to the entire `<dataset>` node — any dataset with "4.0" anywhere in coordinates, methods, or version numbers would incorrectly be marked open access.

---

## Bug Fix Summary (v1.0 → v1.1.0)

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

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `$default-publisher` | `LifeWatch ERIC` | Publisher when no creator org is available |
| `$catalogue-url` | `https://metadatacatalogue.lifewatch.eu/...` | Base URL for catalogue record links |

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
| `coverage/temporalCoverage` | `dates[@dateType='Collected']` | Not mapped |
| `project/funding` | `fundingReferences` | Not mapped |
| `licensed/url` | `rights/@rightsURI` | Not mapped |
| `methods` | `description[@descriptionType='Methods']` | Not mapped |
| `geographicCoverage` point | `geoLocationPoint` | Only `geoLocationBox` mapped |

---

## See Also

- [DataCite Metadata Schema 4.x](https://schema.datacite.org/meta/kernel-4/)
- [OpenAIRE Guidelines v4](https://openaire-guidelines-for-literature-repository-managers.readthedocs.io/)
- [EML 2.2.0 specification](https://eml.ecoinformatics.org/)
- [Transformation diagram](docs/transformation-diagram.svg)
- [Field mapping reference](docs/mapping-notes.md)
- [Repository README](../../README.md)
