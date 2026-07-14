# ISO 19139 → DataCite 4.0.1 (OpenAIRE) — Field Mapping Notes

Source namespace: `gmd = http://www.isotc211.org/2005/gmd` (character values wrapped in
`gco = http://www.isotc211.org/2005/gco`).
Target: `oaire:resource` (OpenAIRE Guidelines for Literature Repository Managers v4,
`datacite:` elements from DataCite Metadata Schema 4.0.1).

Field list and worked INPUT/OUTPUT examples below are taken from
`ISO19139 - to - DataCite4.1.xlsx` — two sheets, "Workflow" and "VRE", one row per
ISO 19139 element. Both resource types share the exact same field mapping; only the
fixed `resourceType` pair differs (see below). All XPaths are relative to
`/gmd:MD_Metadata` unless stated otherwise. `$ident` = `gmd:identificationInfo/*[1]`,
`$citation` = `$ident/gmd:citation/gmd:CI_Citation`.

Sibling transformation [`EML220_to_DataCite401`](../../EML220_to_DataCite401) targets
the same `oaire:resource` vocabulary from an EML 2.2.0 source, for `Dataset`
resources. Element order and attribute conventions here (`creatorName
nameType="Personal"`, `rightsList` shape, `alternateIdentifier
alternateIdentifierType="PackageID"`) intentionally match it.

---

## Fields mapped from the source record

| DataCite/OAIRE field | Source | Notes |
|---|---|---|
| `datacite:alternateIdentifiers/alternateIdentifier[@alternateIdentifierType='PackageID']` | `gmd:fileIdentifier/gco:CharacterString` | |
| `datacite:titles/title` | `$citation/gmd:title/gco:CharacterString` | No `xml:lang` — not part of this sheet's mapping (unlike `EML220_to_DataCite401`, which has a source language field) |
| `datacite:publisher` | fixed `"LifeWatch ERIC"` | `$default-publisher` param |
| `datacite:dates/date[@dateType='Issued']` | `$citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:Date` | |
| `datacite:descriptions/description[@descriptionType='Abstract']` | `$ident/gmd:abstract/gco:CharacterString` | |
| `datacite:subjects/subject` | `$ident/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString` | Plain values, no `subjectScheme` — this sheet has no thesaurus column (unlike `EML220_to_DataCite401`) |
| `datacite:creators` / `datacite:contributors` | every `gmd:CI_ResponsibleParty` in the record | Routed by `gmd:role/gmd:CI_RoleCode/@codeListValue` through the table below |
| `datacite:rightsList/rights` | `$ident/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString` | `rightsIdentifier` = the literal license text, `rightsIdentifierScheme="SPDX"`. Text content is always the literal `"open access"`, matching the sheet's worked example verbatim (not derived from the license itself — see Known Limitations) |
| `datacite:identifier[@identifierType='DOI']` | a `gmd:distributionInfo//gmd:CI_OnlineResource` where `gmd:protocol = 'DOI'` or the linkage URL contains `doi.org` | First match wins |

## Fields fixed per resource type ("we can put here always ...")

| Field | `$resource-type = 'Workflow'` | `$resource-type = 'VRE'` |
|---|---|---|
| `datacite:resourceType/@resourceTypeGeneral` | `Workflow` | `InteractiveResource` |
| `oaire:resourceType/@resourceTypeGeneral` | `other research product` | `other research product` |
| `oaire:resourceType/@uri` | `http://purl.org/coar/resource_type/c_393c` | `http://purl.org/coar/resource_type/c_e9a0` |
| `oaire:resourceType` text | `workflow` | `interactive resource` |

## Responsible-party routing table

Verbatim from the source sheet's "point of contact" row, COMMENTS column:

| `gmd:role` codeListValue | DataCite target |
|---|---|
| `author` | `creator` |
| `creator` | `creator` |
| `owner` | `creator` |
| `associated party` | `contributor`, `contributorType="RelatedPerson"` |
| `custodian` | `contributor`, `contributorType="DataManager"` |
| `distributor` | `contributor`, `contributorType="Distributor"` |
| `point of contact` | `contributor`, `contributorType="ContactPerson"` |
| `principal investigator` | `contributor`, `contributorType="Supervisor"` |
| `processor` | `contributor`, `contributorType="DataCurator"` |
| `resource provider` | `contributor`, `contributorType="Producer"` |
| `user` | `contributor`, `contributorType="Researcher"` |

Creator/contributor names are split "Given Surname" → "Surname, Given" using the same
last-whitespace-token heuristic as `ISO19139_to_EML220` (comma-separated source data
splits cleanly; multi-word surnames without a comma do not — see that stylesheet's
Known Limitations).

---

## Additions beyond the literal sheet

Two (DataCite-mandatory) fields have no explicit row in the source sheet. Both are
added here so the output is always schema-valid, not left empty:

| Field | Added value | Why |
|---|---|---|
| `datacite:identifier` (primary) | Falls back to `identifierType="URL"` = `$catalogue-base-url` + `fileIdentifier` when no DOI is found | The sheet's own COMMENTS column on the "distribution info" row asks the open question "what about the other links?" and leaves it unresolved. DataCite requires a primary identifier, so a deterministic fallback is used rather than leaving it empty. |
| `datacite:publicationYear` | First 4 characters of the same publication date already mapped to `datacite:date[@dateType='Issued']` | DataCite-mandatory; not an explicit row in the sheet, but a direct derivation of data already extracted, not an invented value. |

---

## Known Limitations

| Area | Limitation |
|---|---|
| `creation date`, `revision date`, `status` | The source sheet marks all three "Not mapped" — intentionally omitted from the output. |
| `originator` role | Appears in the VRE sheet's own worked example (`gmd:role` = `originator`, for contact "Koen Greuell") but is **not** in the sheet's 11-row routing table. Routed here to `contributor`, `contributorType="Other"` as a documented fallback for any unrecognised role code. |
| VRE worked example's `point of contact` OUTPUT column | The sheet's own VRE sheet shows the *same* creator example as the Workflow sheet (Mancinelli/Giorgio) in this cell — a copy/paste artifact, not a real VRE-specific mapping. This stylesheet applies the general routing table to every `CI_ResponsibleParty` found, regardless of sheet. |
| `rightsList` text | Always the literal `"open access"`, even for restrictive licenses, matching the sheet's own worked example literally. This looks like an oversight in the source sheet — flag before using this output for a non-open license. |
| `rightsURI` lookup | Only `CC-BY-4.0` is proven by the sheet's worked example. `CC-BY-SA-4.0`, `CC0-1.0`, `MIT`, `Apache-2.0` and `GPL-3.0` are included on a best-effort basis per the sheet's own COMMENTS instruction ("put the right link according to the license if possible, e.g. GPL-3.0"); any other license text is emitted without a `rightsURI`. |
| Non-DOI distribution links | Only a DOI-shaped online resource is mapped (to the primary identifier). Other distribution links (e.g. `https://my.lifewatch.eu/workflow/...`, `https://naavre.net`) are dropped — the sheet leaves this as an explicit open question, not a decided mapping. |
| Identification block | `$ident` is `gmd:identificationInfo/*[1]` — works for `gmd:MD_DataIdentification` or `srv:SV_ServiceIdentification`, but only the first identification block is read. |
| Language | Not mapped — this sheet has no `dc:language` row (unlike `EML220_to_DataCite401`). |

---

## See Also

- [OpenAIRE Guidelines for Literature Repository Managers v4](https://openaire-guidelines-for-literature-repository-managers.readthedocs.io/)
- [DataCite Metadata Schema 4.0.1](https://schema.datacite.org/meta/kernel-4.0.1/)
- [ISO 19139 schema (OGC)](http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd)
- [Transformation diagram](transformation-diagram.svg)
- [Sibling: EML220_to_DataCite401](../../EML220_to_DataCite401)
- [Repository README](../../../README.md)
