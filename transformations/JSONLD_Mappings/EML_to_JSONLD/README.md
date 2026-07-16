# EML 2.2.0 → JSON-LD

Converts an **EML 2.2.0** dataset record into a **schema.org `Dataset` JSON-LD**
document, per the LifeWatch ERIC JSON-LD mapping spec.

---

## Overview

| Property | Value |
|---|---|
| Source format | EML 2.2.0 (`https://eml.ecoinformatics.org/eml-2.2.0`) |
| Target format | JSON-LD (`@vocab: https://schema.org/`), `@type: "Dataset"` |
| Scope | Dataset assets only |
| Implementation | Python (Google Colab notebook), not XSLT |
| Notebook | `EML_to_JsonLD_v2_NEW-v5.2.ipynb` |
| Documentation | `docs/EML_to_JsonLD_Documentation_v5.2.pdf` (7 pages) |
| Version | 5.2 — 2026-07-14 |
| Status | Documented, in active use — see version history below |
| Author | LifeWatch ERIC |

Unlike the XSLT-based transformations elsewhere in this repository, this is a
self-contained **Google Colab notebook**: it installs its own dependencies
(`lxml`, `tabulate`) on first run, prompts for a file upload, converts, validates,
and downloads the result — no local environment setup required.

---

## Purpose

Within the broader LifeWatch ERIC JSON-LD framework (Workflows → `CreativeWork`,
VREs → `CreativeWork`, Services → `Action`/`HowTo` — see
[`../ISO19139_to_JSONLD`](../ISO19139_to_JSONLD)), this notebook handles **Dataset**
assets specifically, converting native EML 2.2.0 records into schema.org-compliant
JSON-LD for discovery and harvesting.

---

## File Structure

```
EML_to_JSONLD/
├── EML_to_JsonLD_v2_NEW-v5.2.ipynb   ← the converter notebook
├── docs/
│   └── EML_to_JsonLD_Documentation_v5.2.pdf   ← full technical documentation (7 pages)
└── README.md                          ← this file
```

---

## Identifier strategy

| EML source | JSON-LD output | Priority |
|---|---|---|
| DOI `alternateIdentifier` (`doi.org/10.48372/{UUID}`) | `@id` + `url` | 1 — GeoNetwork UUID |
| `@packageId` attribute | `@id` + `url` | 2 — fallback |
| other `alternateIdentifier` URLs (handle, DOI) | `sameAs` | all non-UUID identifiers |
| `distribution/online/url` | `sameAs` (merged, deduped) | additional download links |

## Mapping summary

| EML field | Status | JSON-LD output |
|---|---|---|
| `title` | OK | `name` |
| `shortName` | OK | `alternateName` |
| `abstract/para` | OK | `description` |
| `pubDate` | OK | `datePublished` |
| `language` | OK | `inLanguage` |
| `purpose`, `additionalInfo` | OK | same-named custom extension properties |
| `maintenance` | OK | `maintenance {description, frequency}` |
| `creator` | OK | `creator` (Person/Organization) |
| `associatedParty` | OK | `contributor` |
| `publisher` | OK | `publisher` |
| `metadataProvider` | **DROPPED** | no schema.org equivalent (as of v5.2) |
| `contact` | **PARTIAL** | skipped — `contactPoint` is invalid on `Dataset` per the validator |
| — | OK | `provider` — hardcoded LifeWatch ERIC organisation block (v5.2, see below) |
| `licensed/url` or CC URL in `intellectualRights` | OK | `license` |
| `keywordSet/keyword` (+ `keywordThesaurus`) | OK | `keywords[]` — `DefinedTerm` when thesaurus present, plain string otherwise |
| `geographicCoverage` | OK | `spatialCoverage` (`Place` + `GeoShape.box`) |
| `temporalCoverage` | OK | `temporalCoverage` (ISO 8601 interval or single date) |
| `dataTable`/`otherEntity` attribute | OK | `variableMeasured[]` (`PropertyValue`) |
| `project/funding` | OK | `funder` (Organization) |
| `project/title` | **PARTIAL** | no schema.org slot |

Full field-by-field detail, including the party/rights/coverage/attribute mapping
tables, is in `docs/EML_to_JsonLD_Documentation_v5.2.pdf`, sections 4–5.

## Built-in validation

`validate_jsonld()` runs automatically after every conversion and checks: `@context`
is `{"@vocab": "https://schema.org/"}`; `@type` is `"Dataset"`; `@id` is present and
contains `/srv/api/records/{uuid}`; `url`, `name`, `description`, `creator` are
present; `sameAs` items are plain URL strings, not objects; and that forbidden keys
(`about`, `identifier`, `contactPoint`, `dcterms:title`, `schema:name`,
`distribution`) are absent. External validation: <https://validator.schema.org/>.

---

## Usage

### Google Colab (primary workflow)

Runtime → Restart runtime → Runtime → Run all, then upload your EML 2.2.0 XML file
when prompted. The resulting `.jsonld` file downloads automatically.

### Programmatic

```python
# Option A — via the run() helper
result = run(xml_path='/path/to/record.xml', output_path='record.jsonld')

# Option B — direct class usage
conv = EML2JsonLD('/path/to/record.xml')
doc = conv.convert()
conv.save('record.jsonld')
conv.print_loss_report()
```

### Mapping report status codes

| Status | Meaning |
|---|---|
| `OK` | Field successfully mapped to JSON-LD output |
| `PARTIAL` | Attempted but no schema.org slot available |
| `LOST` | EML element absent in the source file (not a code error) |
| `DROPPED` | Field intentionally excluded per spec (e.g. `metadataProvider`) |

---

## Version History

| Version | Change |
|---|---|
| v5.2 | `provider` hardcoded to the LifeWatch ERIC block; `metadataProvider` dropped (no schema.org equivalent); `lxml` `FutureWarning` fixed in `parse_geographic()`. |
| v5.1 | `sameAs` restricted to plain URL strings per spec row 18. |
| v5.0 | UUID priority reordered: DOI `alternateIdentifier` before `packageId`. |
| v4.x | Initial `alternateIdentifier` / distribution URL merge for `sameAs`. |
| v3.x | Semantic annotation support in attribute/`PropertyValue` mapping. |

---

## See Also

- [ISO19139 → JSON-LD (Workflows, VREs, Services)](../ISO19139_to_JSONLD)
- [schema.org validator](https://validator.schema.org/)
- [JSONLD_Mappings overview](../README.md)
- [Repository README](../../../README.md)
