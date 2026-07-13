# ISO 19139 → EML 2.2.0 — Field Mapping Notes

Source namespace: `gmd = http://www.isotc211.org/2005/gmd` (character values wrapped in
`gco = http://www.isotc211.org/2005/gco`), temporal extents in
`gml = http://www.opengis.net/gml`.
Target namespace: `eml = https://eml.ecoinformatics.org/eml-2.2.0`.

All XPaths below are relative to `/gmd:MD_Metadata` unless stated otherwise. `$ident` =
`gmd:identificationInfo/gmd:MD_DataIdentification`, `$citation` = `$ident/gmd:citation/gmd:CI_Citation`.

---

## ① `packageId` / `alternateIdentifier`

| Target | Source |
|---|---|
| `eml:eml/@packageId` | `gmd:fileIdentifier/gco:CharacterString` (or the `$package-id` param override) |
| `dataset/alternateIdentifier` (one per match) | every `$citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString` |

No identifier is treated as authoritative over another — a DOI and a catalogue handle both become
`alternateIdentifier` entries, in document order.

## ② `title`

`$citation/gmd:title/gco:CharacterString` → `dataset/title`, `normalize-space()` applied.

## ③ `creator` / ④ `metadataProvider` / ⑤ `associatedParty`

ISO 19139 has a flat list of `gmd:CI_ResponsibleParty` at two structurally different levels, and
EML splits people into distinct role-typed elements. The mapping:

| ISO 19139 location | `gmd:role` code | EML target |
|---|---|---|
| `$citation/gmd:citedResponsibleParty` | `originator`, `author` | `dataset/creator` |
| `/gmd:MD_Metadata/gmd:contact` (top-level, i.e. the **metadata record's own** contact) | any | `dataset/metadataProvider` |
| `$citation/gmd:citedResponsibleParty` | anything else (`publisher`, `custodian`, `distributor`, `resourceProvider`, `principalInvestigator`, ...) | `dataset/associatedParty`, with `<role>` set from the code via the `role-label` template |
| `$ident/gmd:pointOfContact` | any | `dataset/contact` (see ⑬) |

Each party is rendered by the shared `emit-party` named template:

| EML field | ISO source | Notes |
|---|---|---|
| `individualName/givenName` + `individualName/surName` | `gmd:individualName/gco:CharacterString` | Split heuristically — see **Known Limitations** |
| `organizationName` | `gmd:organisationName/gco:CharacterString` | Omitted when empty |
| `positionName` | `gmd:positionName/gco:CharacterString` | Omitted when empty |
| `electronicMailAddress` | `gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString` | Omitted when empty |

`individualName` is omitted entirely when the source has no `gmd:individualName` (organisation-only
parties), matching EML's `ResponsiblePartyType`, which does not require an individual name.

## ⑥ `pubDate`

`$citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue = 'publication']/gmd:date/gco:Date`,
falling back to `/gmd:MD_Metadata/gmd:dateStamp` when no citation date is typed `publication`.
Omitted entirely when neither is present (no empty `<pubDate/>` is ever emitted).

## ⑦ `language`

`$ident/gmd:language/gmd:LanguageCode/@codeListValue` (falling back to the top-level
`/gmd:MD_Metadata/gmd:language`), converted from an ISO 639-1/639-2 code to the full English word
via the `iso639-to-word` named template (`eng`/`en` → `English`, `ita`/`it` → `Italian`, `fra`/`fre`/`fr`
→ `French`, `deu`/`ger`/`de` → `German`, `spa`/`es` → `Spanish`, `por`/`pt` → `Portuguese`,
`nld`/`dut`/`nl` → `Dutch`, `ell`/`gre`/`el` → `Greek`). Unrecognised codes pass through unchanged.

## ⑧ `abstract`

`$ident/gmd:abstract/gco:CharacterString` → `dataset/abstract/para` (single paragraph — ISO 19139
carries the abstract as one string, unlike EML's own multi-`<para>` abstracts).

## ⑨ `keywordSet`

One `keywordSet` per `$ident/gmd:descriptiveKeywords/gmd:MD_Keywords`:

| EML field | ISO source |
|---|---|
| `keyword` (one per match) | `gmd:keyword/gco:CharacterString` |
| `keywordThesaurus` | `gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString`, or the literal `"none"` when absent — the attribute-equivalent element is always present, never omitted |

## ⑩ `intellectualRights`

Every `gmd:useLimitation/gco:CharacterString` under `$ident/gmd:resourceConstraints/*` becomes its
own `<para>` inside a single `intellectualRights` block. The wildcard step matches
`MD_LegalConstraints`, `MD_SecurityConstraints` or the base `MD_Constraints`, whichever the source
uses. Omitted entirely when no `useLimitation` text is present.

## ⑪ `distribution`

`gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource`
entries with a non-empty `gmd:linkage/gmd:URL` become `distribution/online`:

| EML field | ISO source |
|---|---|
| `onlineDescription` | `gmd:name/gco:CharacterString` (omitted when empty) |
| `url` | `gmd:linkage/gmd:URL` |

`gmd:protocol` is not mapped — EML's `online/url` has no protocol attribute of its own.

## ⑫ `coverage`

**Geographic** — one `geographicCoverage` per
`$ident/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox`:

| EML field | ISO source |
|---|---|
| `geographicDescription` | sibling `gmd:EX_Extent/gmd:description/gco:CharacterString`, or the literal `"Not provided"` when absent (EML requires this element) |
| `boundingCoordinates/westBoundingCoordinate` | `gmd:westBoundLongitude/gco:Decimal` |
| `boundingCoordinates/eastBoundingCoordinate` | `gmd:eastBoundLongitude/gco:Decimal` |
| `boundingCoordinates/northBoundingCoordinate` | `gmd:northBoundLatitude/gco:Decimal` |
| `boundingCoordinates/southBoundingCoordinate` | `gmd:southBoundLatitude/gco:Decimal` |

**Temporal** — one `temporalCoverage` per
`$ident/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent`:

| ISO `gmd:extent` child | EML target |
|---|---|
| `gml:TimePeriod` | `rangeOfDates/beginDate/calendarDate` ← `gml:beginPosition`, `rangeOfDates/endDate/calendarDate` ← `gml:endPosition` |
| `gml:TimeInstant` | `singleDateTime/calendarDate` ← `gml:timePosition` |

The whole `coverage` block is omitted when the source has neither a bounding box nor a temporal
extent.

## ⑬ `contact`

`$ident/gmd:pointOfContact/gmd:CI_ResponsibleParty` (resource-level point of contact, any role code)
→ `dataset/contact`. This is distinct from the top-level `/gmd:MD_Metadata/gmd:contact`, which is the
contact for the *metadata record itself* and maps to `metadataProvider` (see ④).

---

## Element ordering

EML 2.2.0's `resourceGroup` is a strict `xsd:sequence`. The stylesheet emits dataset children in
schema order: `alternateIdentifier*, title, creator+, metadataProvider*, associatedParty*, pubDate?,
language?, abstract?, keywordSet*, intellectualRights?, distribution*, coverage?, contact+`. Building
in any other order produces schema-invalid output even though the individual field mappings are
correct — this bit the DataCite stylesheet's early drafts and is called out here so it isn't
repeated.

---

## Known Limitations

| Area | Limitation |
|---|---|
| Name splitting | `gmd:individualName` is a single free-text string. The stylesheet prefers `"Surname, Given"` (splits on the comma); otherwise it treats the **last** whitespace-delimited token as the surname and everything before it as the given name. Multi-word surnames (e.g. "van der Berg") or "Surname Given" orderings without a comma will split incorrectly. Prefer comma-separated source data where possible. |
| `dataTable` / attribute metadata | ISO 19139 has no per-column data-dictionary equivalent to EML's `attributeList`. Nothing is emitted for `dataTable`; add it manually downstream if the dataset has tabular content. |
| `methods` / `project` | Not present in `MD_DataIdentification` and therefore not mapped. Populate manually if needed. |
| `gmd:role` beyond originator/author/publisher | Any other cited role becomes `associatedParty` with a best-effort label (`role-label` template); unrecognised codes are passed through verbatim as the role text rather than guessed at. |
| Multiple `gmd:pointOfContact` | All are emitted as separate `dataset/contact` entries — EML allows repetition, so no data is dropped, but downstream consumers that expect a single "the" contact should pick the first. |
| `gmd:resourceConstraints` other than `useLimitation` | `accessConstraints` / `otherConstraints` / `useConstraints` code-list values are not mapped, only the free-text `useLimitation`. |
| Language fallback | Codes outside the built-in `iso639-to-word` table (see ⑦) are copied through as-is rather than resolved — e.g. `"cat"` (Catalan) stays `"cat"` rather than becoming `"Catalan"`. |

---

## See Also

- [ISO 19115/19139 core (OGC schemas)](http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd)
- [EML 2.2.0 specification](https://eml.ecoinformatics.org/)
- [Transformation diagram](transformation-diagram.svg)
- [Repository README](../../../README.md)
