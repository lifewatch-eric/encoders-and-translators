# ISO 19139 → EOSC Service — Field Mapping Notes

Source namespace: `gmd = http://www.isotc211.org/2005/gmd` (character values wrapped in
`gco = http://www.isotc211.org/2005/gco`).
Target: JSON payload of an EOSC Resource of type `Service`, per the
[EOSC resources model](https://github.com/EOSC-PLATFORM/eosc-resources-model#service).

Field list and source recipes below are taken verbatim from
`ISO19139_to_EOSC_profile.xlsx` ("Resource" and "Mapping with categories" sheets) —
the mapping spreadsheet linked from the transformations tracker for this entry.
All XPaths are relative to `/gmd:MD_Metadata` unless stated otherwise. `$ident` =
`gmd:identificationInfo/*[1]` (the first identification block — `MD_DataIdentification`
in every LifeWatch record seen so far), `$citation` = `$ident/gmd:citation/gmd:CI_Citation`.

---

## Fields mapped from the source record

| EOSC field | Source | Notes |
|---|---|---|
| `name` | `$citation/gmd:title/gco:CharacterString` | `normalize-space()` applied |
| `description` | `$ident/gmd:abstract/gco:CharacterString` | `normalize-space()` applied |
| `publishingDate` | `$citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:Date` | Falls back to `/gmd:MD_Metadata/gmd:dateStamp` when no citation date is typed `publication` — not specified in the source sheet, added so the (Mandatory) field is never empty |
| `publicContacts` | every distinct `gmd:electronicMailAddress/gco:CharacterString` anywhere in the record | Source sheet says "the electronicMailAddress of all points of contacts" — implemented as every email in the document (`contact` + every `pointOfContact`), deduplicated |
| `webpage` / `urls[0]` | `concat($catalogue-base-url, gmd:fileIdentifier/gco:CharacterString)` | `$catalogue-base-url` defaults to `https://metadatacatalogue.lifewatch.eu/srv/api/records/`, matching the source sheet's worked example |
| `urls[1..]` | every distinct `gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL` | |
| `alternativePIDs` | online resources under the same `distributionInfo` block where `gmd:protocol/gco:CharacterString = 'DOI'` | `pid` = the resource's `linkage/URL` (falls back to `name` if URL absent); `pidSchema` is always the literal `"DOI"` |
| `tags` | every distinct `gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString` anywhere in `$ident` | Same pattern as `EML211_to_EML220`'s `keywordSet` — all keyword blocks are flattened into one free-text tag list, since EOSC `tags` has no thesaurus concept |
| `trl` | `.//gmd:serviceTRL_service/gmd:LW_ServiceTRL_service/@codeListValue`, e.g. `"TRL 9 – Actual system proven in operational environment"` | The digits after `"TRL "` and before the next space are extracted and prefixed with `trl-` (→ `trl-9`). This is a **LifeWatch-specific ISO 19139 extension element**, not part of the ISO 19139/gmd standard — see Known Limitations |

## Fields fixed per the source sheet ("we can put here always ...")

These are not derived from the ISO 19139 record. The source sheet gives one fixed
value for LifeWatch ERIC's own registration and says to use it every time; each is
exposed as a stylesheet parameter so a caller can override it without editing the XSLT.

| EOSC field | Fixed value | Parameter |
|---|---|---|
| `type` | `"Service"` | — (this stylesheet is Service-only by design) |
| `nodePID` | `21.T15999/LifeWatch-ERIC` | `$node-pid` |
| `resourceOwner` | `21.11174/PTokiF00` | `$resource-owner-pid` |
| `logo` | LifeWatch ERIC logo URL | `$logo-url` |
| `scientificDomains` | `[{"scientificDomain": "scientific_domain-natural_sciences", "scientificSubdomain": "scientific_subdomain-natural_sciences-biological_sciences"}]` | not parameterised — the source sheet gives no override case |
| `accessTypes` | `access_type-virtual` | `$access-type` |
| `jurisdiction` | `ds_jurisdiction-global` | `$jurisdiction` |

## `categories` — LifeWatch category keyword → EOSC category/subcategory

The "Resource" sheet's `categories` row points to a second table ("Mapping with
categories") that maps the LifeWatch catalogue's own service-category picklist to
EOSC category/subcategory vocabulary ids. **ISO 19139 has no field that reliably
carries this picklist value** (it is a catalogue-UI concept, not a metadata element),
so the stylesheet takes it as the `$service-category` parameter (default `'support'`)
and looks it up via the `eosc-category-id` / `eosc-subcategory-id` named templates:

| LifeWatch category | EOSC category | EOSC subcategory |
|---|---|---|
| `data access` | `category-processing_and_analysis-data_management` | `subcategory-processing_and_analysis-data_management-discovery` |
| `data processing` | `category-processing_and_analysis-data_analysis` | `subcategory-processing_and_analysis-data_analysis-data_extrapolation` |
| `data classification` | `category-processing_and_analysis-data_analysis` | `subcategory-processing_and_analysis-data_analysis-data_extrapolation` |
| `modelling` | `category-sharing_and_discovery-development_resources` | `subcategory-sharing_and_discovery-development_resources-software_libraries` |
| `collaborative coding` | `category-sharing_and_discovery-applications` | `subcategory-aggregators_and_integrators-aggregators_and_integrators-applications` |
| `support` | `category-sharing_and_discovery-applications` | `subcategory-aggregators_and_integrators-aggregators_and_integrators-applications` |
| `help desk` | `category-training_and_support-consultancy_and_support` | `subcategory-security_and_operations-operations_and_infrastructure_management_services-helpdesk` |
| `training platform` | `category-training_and_support-education_and_training` | `subcategory-training_and_support-education_and_training-training_platform` |
| `training catalogue` | `category-training_and_support-education_and_training` | `subcategory-training_and_support-education_and_training-training_platform` |

Run with `python3 run.py --service-category "data access"` (or the equivalent XSLT
`service-category` parameter) to pick a different row. Unrecognised values fall back
to the `support` row.

---

## Known Limitations

| Area | Limitation |
|---|---|
| `id` | Never emitted. The source sheet marks it `auto-gen` — EOSC assigns this PID when the resource is registered through the platform, so a client-side stylesheet has nothing meaningful to put there. |
| `serviceProviders` | Not mapped. The source sheet lists it as Recommended but gives no mapping recipe from ISO 19139 — populate manually in the EOSC portal. |
| `termsOfUse`, `privacyPolicy`, `accessPolicy`, `orderType`, `order`, `relatedInteroperabilityGuidelines` | Not mapped — the source sheet leaves these rows without a `Mapping` value at all. All are Optional in the EOSC model; fill them in manually after registration if applicable. |
| `categories` | As above — ISO 19139 carries no equivalent field, so this is a parameter (`$service-category`), not a derived value. Get it wrong and the record lands in the wrong EOSC catalogue category. |
| `trl` | Depends on the non-standard `gmd:serviceTRL_service` / `gmd:LW_ServiceTRL_service` extension element existing in the source record. Records without it produce `"trl": ""`, which is **not valid** against the EOSC schema (`trl` is Mandatory) — the caller must patch this in before submission if the source catalogue entry has no TRL assigned. |
| `alternativePIDs` / DOI detection | Only online resources whose `gmd:protocol` is the exact literal `DOI` are picked up. A record that expresses a DOI a different way (e.g. only as a bare string in `gmd:linkage/gmd:URL` without a `DOI` protocol tag) will not be detected. |
| `publishingDate` fallback | The source sheet's mapping recipe only names the `publication`-typed citation date; the `gmd:dateStamp` fallback used here to avoid emitting an empty Mandatory field is an addition, not part of the original recipe — verify it's an acceptable substitute for records that only carry a metadata date stamp. |
| Identification block | `$ident` is taken as `gmd:identificationInfo/*[1]` so the stylesheet works whether the source uses `gmd:MD_DataIdentification` or ISO 19119's `srv:SV_ServiceIdentification` — but only one identification block is read; a record with more than one is only partially mapped. |

---

## See Also

- [EOSC resources model — Service](https://github.com/EOSC-PLATFORM/eosc-resources-model#service)
- [ISO 19139 schema (OGC)](http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd)
- [Transformation diagram](transformation-diagram.svg)
- [Repository README](../../../README.md)
