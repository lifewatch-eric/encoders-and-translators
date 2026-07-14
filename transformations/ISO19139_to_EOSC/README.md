# ISO 19139 → EOSC Service

Transforms an **ISO 19139** (`gmd:MD_Metadata`) service metadata record into the JSON
payload of an **EOSC Resource of type `Service`**, per the
[EOSC resources model](https://github.com/EOSC-PLATFORM/eosc-resources-model#service),
so LifeWatch services registered in the metadata catalogue can be published to the
EOSC Beyond marketplace.

---

## Overview

| Property | Value |
|---|---|
| Source format | ISO 19139 (`http://www.isotc211.org/2005/gmd`) |
| Target format | EOSC Resource — `Service` (JSON) |
| Output | JSON text (not XML) |
| XSLT version | 1.0 |
| Stylesheet | `xslt/main.xsl` |
| Version | 1.1.0 |
| Status | 🚧 In progress — mapping complete, core fields implemented, output validated against the real [EOSC JSON Schema](docs/eosc-schema/); several optional EOSC fields are intentionally unmapped (see [Known Limitations](docs/mapping-notes.md#known-limitations)) |
| Program | EOSC Beyond |
| Author | LifeWatch ERIC Service Centre |
| License | MIT |

---

## Purpose

The LifeWatch metadata catalogue exports its services as ISO 19139 records. EOSC
Beyond expects resources in its own JSON model instead. This stylesheet lifts the
fields the mapping sheet (`ISO19139_to_EOSC_profile.xlsx`) identifies as derivable
from ISO 19139 — title, abstract, publication date, contact emails, distribution
URLs/DOIs, keywords, and the LifeWatch service-TRL extension — into that JSON shape,
alongside the fixed defaults LifeWatch ERIC registers every service with (node PID,
resource owner, logo, scientific domain, access type, jurisdiction).

```
ISO 19139 (gmd:MD_Metadata, hierarchyLevel=service)
       │
       ▼  xslt/main.xsl
EOSC Resource "Service" (JSON)
       │
       ▼  submitted via the EOSC Beyond onboarding process
EOSC Marketplace
```

---

## File Structure

```
ISO19139_to_EOSC/
├── xslt/
│   └── main.xsl                                    ← transformation stylesheet (v1.1.0)
├── examples/
│   ├── input/
│   │   ├── semantic-platform-service-iso19139.xml  ← full-featured sample (DOI, keywords, TRL)
│   │   └── minimal-sample-service-iso19139.xml     ← minimal / edge-case sample
│   └── output/
│       ├── semantic-platform-service-eosc-service.json
│       └── minimal-sample-service-eosc-service.json
├── docs/
│   ├── mapping-notes.md                            ← field-level mapping reference
│   ├── transformation-diagram.svg                  ← visual flow diagram (open in browser)
│   └── eosc-schema/                                ← vendored real EOSC JSON Schemas + patch notes
│       ├── eosc-resource.schema.json
│       ├── service.schema.json
│       └── README.md
├── run.py                                           ← one-command transform + test runner
├── test_transformation.py                           ← automated test suite
├── validate_output.py                               ← validates output against the real EOSC schema
└── README.md                                        ← this file
```

---

## Transformation Diagram

Open `docs/transformation-diagram.svg` in any browser to see the visual flow of the
transformation steps, or read the field-by-field breakdown in `docs/mapping-notes.md`.

---

## Mapping Summary

| EOSC field | ISO 19139 source |
|---|---|
| `name` | `citation/title` |
| `description` | `MD_DataIdentification/abstract` |
| `publishingDate` | citation date typed `publication`, else `dateStamp` |
| `publicContact` | every `electronicMailAddress` in the record |
| `webpage`, `url[0]` | `$catalogue-base-url` + `fileIdentifier` |
| `url[1..]` | `distributionInfo//CI_OnlineResource/linkage/URL` |
| `alternativePIDs` | online resources with `protocol = DOI` |
| `tags` | `descriptiveKeywords/MD_Keywords/keyword` |
| `trl` | `serviceTRL_service/LW_ServiceTRL_service/@codeListValue` |
| `type`, `nodePID`, `resourceOwner`, `logo`, `scientificDomains` (object), `accessType`, `jurisdiction` | fixed defaults (parameterised) |
| `categories` | `$service-category` parameter, looked up against the LifeWatch → EOSC category table |

Field names above match the real `eosc-resource.schema.json` / `service.schema.json`
(`url`, `publicContact`, `accessType` — all singular; `scientificDomains` is an
object, not an array). The source spreadsheet's own worked examples used different
names/shapes for these four — see
[mapping-notes.md, "Validated against the real EOSC schema"](docs/mapping-notes.md#validated-against-the-real-eosc-schema).

See [docs/mapping-notes.md](docs/mapping-notes.md) for the full field-level reference,
including every field left unmapped and why.

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `$catalogue-base-url` | `https://metadatacatalogue.lifewatch.eu/srv/api/records/` | Prefixed to `fileIdentifier` to build `webpage` / `url[0]` |
| `$node-pid` | `21.T15999/LifeWatch-ERIC` | Value written to `nodePID` |
| `$resource-owner-pid` | `21.11174/PTokiF00` | Value written to `resourceOwner` |
| `$logo-url` | LifeWatch ERIC logo | Value written to `logo` |
| `$service-category` | `support` | LifeWatch category keyword driving `categories[]` — see [mapping-notes.md](docs/mapping-notes.md#categories--lifewatch-category-keyword--eosc-categorysubcategory) |
| `$access-type` | `access_type-virtual` | Value written to `accessType` |
| `$jurisdiction` | `ds_jurisdiction-global` | Value written to `jurisdiction` |

---

## Quick Start

```bash
pip install lxml
cd transformations/ISO19139_to_EOSC

# Drop your ISO 19139 service record into examples/input/ then:
python3 run.py

# Output appears in examples/output/ automatically.
python3 run.py --force                       # re-run even when output exists
python3 run.py --service-category "data access"
```

### run.py Flags

```bash
python3 run.py                                     # all new inputs
python3 run.py --force                             # re-run all
python3 run.py --input examples/input/file.xml     # single file
python3 run.py --output /path/to/result.json       # custom output path
python3 run.py --node-pid 21.T15999/Other-Node
python3 run.py --service-category "training platform"
python3 run.py --no-tests                          # transform only
python3 run.py --open-folder                       # open output/ in Finder
python3 run.py --quiet                             # summary only
```

### test_transformation.py

```bash
python3 test_transformation.py                              # bundled sample
python3 test_transformation.py --input your-file.xml         # your file
python3 test_transformation.py --input f.xml --output r.json # test + save
```

### validate_output.py — check against the real EOSC schema

```bash
pip install jsonschema referencing
python3 validate_output.py examples/output/*.json
```

Validates output against the vendored `docs/eosc-schema/` copies of the real
`eosc-resource.schema.json` / `service.schema.json` from
[EOSC-PLATFORM/eosc-resources-model](https://github.com/EOSC-PLATFORM/eosc-resources-model),
not just against the source spreadsheet's own (partly incorrect) worked examples. See
[mapping-notes.md, "Validated against the real EOSC schema"](docs/mapping-notes.md#validated-against-the-real-eosc-schema).

---

## Known Limitations

See the [Known Limitations](docs/mapping-notes.md#known-limitations) section of the
mapping notes — notably: `id` is never emitted (EOSC assigns it on registration and
the schema requires it, so this is an expected, non-blocking validation error every
time), `publicContact` fails schema validation (`minItems: 1`) when the source record
has no contact email at all, `categories` depends on a manual `$service-category`
parameter since ISO 19139 has no equivalent field, and `trl` requires the
non-standard `serviceTRL_service` extension element to be present in the source
record.

---

## See Also

- [EOSC resources model — Service](https://github.com/EOSC-PLATFORM/eosc-resources-model#service)
- [Vendored EOSC JSON Schemas + patch notes](docs/eosc-schema/README.md)
- [ISO 19139 schema (OGC)](http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd)
- [Field mapping reference](docs/mapping-notes.md)
- [Repository README](../../README.md)
