# Mapping Notes — EML 2.2.0 → DataCite 4.0.1

This document describes every field-level decision made in `xslt/main.xsl`, including all bugs found in the original v1.0 draft and how each was fixed.

---

## 1. Root Element & Namespaces

The output root element is `oaire:resource` — the OpenAIRE Literature and Data Guidelines 4.0 container. It declares all required namespaces inline:

| Prefix | Namespace URI | Purpose |
|---|---|---|
| `oaire` | `http://namespace.openaire.eu/schema/oaire/` | OpenAIRE wrapper + file/resourceType |
| `datacite` | `http://datacite.org/schema/kernel-4` | DataCite 4.0.1 metadata elements |
| `dc` | `http://purl.org/dc/elements/1.1/` | Dublin Core (language only) |
| `xsi` | `http://www.w3.org/2001/XMLSchema-instance` | Schema location |

---

## 2. datacite:identifier

**FIX-6** — the original always built a catalogue URL using the first `alternateIdentifier`, regardless of whether a DOI was present.

| Condition | identifierType | Value |
|---|---|---|
| A DOI `alternateIdentifier` exists (contains "doi") | `DOI` | The full DOI URI |
| No DOI present | `URL` | `$catalogue-url` + non-DOI identifier or packageId |

The DOI detection uses a case-insensitive `translate()` to match "doi", "DOI", etc.

---

## 3. datacite:titles / datacite:title

**FIX-7** — `xml:lang` is now added from EML `./language` when present.

| EML source | DataCite output |
|---|---|
| `dataset/title` | `datacite:titles/datacite:title` |
| `dataset/language` | `xml:lang` attribute on `datacite:title` |

---

## 4. datacite:publisher

**FIX-10** — the original had no `datacite:publisher` element (mandatory in DataCite 4.x).

| Condition | Publisher value |
|---|---|
| `creator[1]/organizationName` is non-empty | First creator's organization |
| Otherwise | `$default-publisher` parameter (default: `"LifeWatch ERIC"`) |

---

## 5. datacite:publicationYear

**FIX-11** — the original had no `datacite:publicationYear` (mandatory in DataCite 4.x).

| EML source | DataCite output |
|---|---|
| `dataset/pubDate` (first 4 chars) | `datacite:publicationYear` |

`substring(./pubDate, 1, 4)` extracts the 4-digit year from any date format (`YYYY-MM-DD` or `YYYY`).

---

## 6. datacite:dates

The full `pubDate` value is preserved in `datacite:date[@dateType='Issued']`.

---

## 7. dc:language

EML `./language` is mapped to `dc:language` (free text; no ISO 639-1 conversion applied).

---

## 8. datacite:descriptions / datacite:description

**FIX-8** — the original used `<dc:description>` (Dublin Core), which is not the DataCite/OpenAIRE element.  
**FIX-4** — the original used `select="./abstract"` which returns empty in most processors because EML 2.2.0 wraps abstract text inside `<para>` children.

| EML source | DataCite output |
|---|---|
| `dataset/abstract/para` (joined with space) | `datacite:descriptions/datacite:description[@descriptionType='Abstract']` |
| `dataset/abstract` (direct text, fallback) | Same, when no `<para>` children exist |

---

## 9. datacite:subjects

Each keyword becomes a `datacite:subject`. The `keywordThesaurus` value is used as `subjectScheme` when it is non-empty and not equal to `"none"` (case-insensitive).

| EML source | DataCite output |
|---|---|
| `keywordSet/keyword` | `datacite:subject` |
| `keywordSet/keywordThesaurus` (≠ "none") | `@subjectScheme` attribute |

---

## 10. File Locations

**FIX-2** — the original had a double-nested `for-each` on the `additionalMetadata` node-set, producing duplicate entries.

Two sources are iterated **exactly once** each:

| Source | Path |
|---|---|
| A: Direct distribution | `dataset/distribution/online/url` |
| B: GBIF physical | `additionalMetadata/metadata/gbif/physical/distribution/online/url` |

For each URL found:
- Contains "doi" (case-insensitive) → `datacite:alternateIdentifiers/datacite:alternateIdentifier[@alternateIdentifierType='DOI']`
- Otherwise → `oaire:file`

---

## 11. datacite:creators

**FIX-3** — the original always emitted `<datacite:nameIdentifier>` even when `userId` was absent, producing empty invalid elements.

| EML source | DataCite output |
|---|---|
| `individualName/givenName` + `individualName/surName` | `datacite:creatorName` as `"Surname, GivenName"` |
| `organizationName` (fallback when no individualName) | `datacite:creatorName` |
| `organizationName` (non-empty) | `datacite:affiliation` |
| `userId` (non-empty only) | `datacite:nameIdentifier[@nameIdentifierScheme='ORCID']` |

> **Name format**: DataCite convention is `Surname, GivenName` (the original used `GivenName Surname`).

---

## 12. datacite:contributors

**FIX-3** applied — same `nameIdentifier` guard as creators.

| EML role | DataCite contributorType |
|---|---|
| `contact` | `ContactPerson` |
| `metadataProvider` | `DataManager` |

---

## 13. datacite:geoLocations

**FIX-1** — the original had wrong DataCite element names for the latitude bounds.

| DataCite 4.x element | EML source | Original (wrong) |
|---|---|---|
| `westBoundLongitude` | `westBoundingCoordinate` | ✅ correct |
| `eastBoundLongitude` | `eastBoundingCoordinate` | ✅ correct |
| **`southBoundLatitude`** | `southBoundingCoordinate` | ❌ was `southBoundLongitude` |
| **`northBoundLatitude`** | `northBoundingCoordinate` | ❌ was `northBoundLongitude` |

`geoLocationPlace` is suppressed when `geographicDescription` is empty. `geoLocationBox` is suppressed when `boundingCoordinates` is absent.

---

## 14. Resource Type

**FIX-9** — `resourceTypeGeneral` capitalised from `"dataset"` to `"Dataset"` (DataCite 4.x spec requires title-case).  
**FIX-12** — `datacite:resourceType` element added (was missing; required by DataCite 4.x alongside the OpenAIRE element).

Both elements are always emitted:

```xml
<datacite:resourceType resourceTypeGeneral="Dataset">Dataset</datacite:resourceType>
<oaire:resourceType resourceTypeGeneral="Dataset"
    uri="http://purl.org/coar/resource_type/c_ddb1">dataset</oaire:resourceType>
```

---

## 15. Access Rights

**FIX-5** — the original tested `contains(., '4.0')` where `.` was the entire `<dataset>` node, so any dataset with "4.0" anywhere in its content (e.g. coordinates, method versions) would be marked open access. Now tested specifically on the `intellectualRights` text.

| Condition (checked on `intellectualRights/para` or `intellectualRights`) | Output |
|---|---|
| Contains "creative commons" (case-insensitive) | CC-BY 4.0 open access |
| Contains "cc-by" (case-insensitive) | CC-BY 4.0 open access |
| Contains "4.0" | CC-BY 4.0 open access |
| Contains "open access" (case-insensitive) | CC-BY 4.0 open access |
| Otherwise | metadata only access |

Open access output:
```xml
<datacite:rights rightsURI="https://creativecommons.org/licenses/by/4.0/"
    rightsIdentifier="CC-BY-4.0"
    rightsIdentifierScheme="SPDX">open access</datacite:rights>
```

---

## 16. Explicitly Out of Scope

| EML 2.2.0 element | DataCite mapping | Status |
|---|---|---|
| `coverage/temporalCoverage` | `datacite:dates[@dateType='Collected']` | Not mapped |
| `project/funding` | `datacite:fundingReferences` | Not mapped |
| `licensed/url` | `datacite:rights/@rightsURI` | Not mapped (intellectualRights text used instead) |
| `methods` | `datacite:description[@descriptionType='Methods']` | Not mapped |

---

*Last updated: 2026-04-14 — LifeWatch ERIC Service Centre*
