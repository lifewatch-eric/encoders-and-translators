# ISO 19139 → EML 2.2.0

Transforms an **ISO 19139** (`gmd:MD_Metadata`) geospatial metadata record into an **EML 2.2.0**
(`eml:eml`) dataset metadata document, letting catalogues that only export ISO 19115/19139 (e.g.
GeoNetwork instances) feed the same EML-based pipelines used for native EML datasets
(`EML211_to_EML220`, `EML220_to_DataCite401`).

---

## Overview

| Property | Value |
|---|---|
| Source format | ISO 19139 (`http://www.isotc211.org/2005/gmd`) |
| Target format | EML 2.2.0 (`https://eml.ecoinformatics.org/eml-2.2.0`) |
| Output root element | `eml:eml` |
| XSLT version | 1.0 |
| Stylesheet | `xslt/main.xsl` |
| Version | 1.0.0 |
| Status | ✅ Stable  all tests passing on both bundled samples |
| Author | LifeWatch ERIC Service Centre (service.centre@lifewatch.eu) |
| License | MIT |

---

## Purpose

LifeWatch ERIC partners and data providers occasionally publish metadata as ISO 19139 records
(commonly exported from a GeoNetwork catalogue) rather than native EML. This stylesheet lets those
records be lifted into EML 2.2.0 so they can flow through the rest of the `transformations/` pipeline
 including onward conversion to DataCite 4.0.1 via `EML220_to_DataCite401`.

```
ISO 19139 (gmd:MD_Metadata)
       │
       ▼  xslt/main.xsl
EML 2.2.0 (eml:eml)
       │
       ▼  transformations/EML220_to_DataCite401
DataCite 4.0.1 / OpenAIRE
```

---

## File Structure

```
ISO19139_to_EML220/
├── xslt/
│   └── main.xsl                                ← transformation stylesheet (v1.0.0)
├── examples/
│   ├── input/
│   │   ├── lesina-phytoplankton-iso19139.xml   ← full-featured ISO 19139 sample
│   │   └── minimal-sample-iso19139.xml         ← minimal / edge-case sample
│   └── output/
│       ├── lesina-phytoplankton-eml220.xml
│       └── minimal-sample-eml220.xml
├── docs/
│   ├── mapping-notes.md                        ← field level mapping reference
│   └── transformation-diagram.svg              ← visual flow diagram (open in browser)
├── run.py                                       ← one command transform + test runner
├── test_transformation.py                       ← automated test suite
└── README.md                                    ← this file
```

---

## Transformation Diagram

Open `docs/transformation-diagram.svg` in any browser to see the visual flow of the transformation
steps, or read the field-by-field breakdown in `docs/mapping-notes.md`.

---

## Transformation Summary

| # | EML target | ISO 19139 source |
|---|---|---|
| ① | `alternateIdentifier*` | `citation/identifier/MD_Identifier/code` |
| ② | `title` | `citation/title` |
| ③ | `creator+` | `citedResponsibleParty` with role `originator` / `author` |
| ④ | `metadataProvider*` | top-level `MD_Metadata/contact` |
| ⑤ | `associatedParty*` | any other `citedResponsibleParty` (role text preserved) |
| ⑥ | `pubDate` | citation date typed `publication`, else `dateStamp` |
| ⑦ | `language` | ISO 639 code → full English word |
| ⑧ | `abstract/para` | `MD_DataIdentification/abstract` |
| ⑨ | `keywordSet*` | `MD_Keywords` (keyword + thesaurusName) |
| ⑩ | `intellectualRights/para*` | `resourceConstraints/*/useLimitation` |
| ⑪ | `distribution/online*` | `MD_DigitalTransferOptions/onLine` |
| ⑫ | `coverage` | `EX_GeographicBoundingBox` + `EX_TemporalExtent` |
| ⑬ | `contact+` | `MD_DataIdentification/pointOfContact` |

See [docs/mapping-notes.md](docs/mapping-notes.md) for the full field-level reference, including
name-splitting rules and known limitations.

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `$package-id` | `''` (empty) | Overrides `eml:eml/@packageId`. When empty, `gmd:fileIdentifier` is used. |
| `$system` | `https://data.lifewatchitaly.eu` | Value written to `eml:eml/@system`. |
| `$schema-mode` | `canonical` | Controls `xsi:schemaLocation` XSD target. Values: `canonical` \| `gbif`. |

---

## Quick Start

```bash
pip install lxml
cd transformations/ISO19139_to_EML220

# Drop your ISO 19139 file into examples/input/ then:
python3 run.py

# Output appears in examples/output/ automatically.
python3 run.py --force    # re-run even when output exists
```

### run.py Flags

```bash
python3 run.py                                     # all new inputs
python3 run.py --force                             # re-run all
python3 run.py --input examples/input/file.xml     # single file
python3 run.py --output /path/to/result.xml        # custom output path
python3 run.py --package-id my.new.id              # override packageId
python3 run.py --system https://my-catalogue.eu    # override system
python3 run.py --no-tests                          # transform only
python3 run.py --open-folder                       # open output/ in Finder
python3 run.py --quiet                             # summary only
```

### test_transformation.py

```bash
python3 test_transformation.py                              # bundled sample
python3 test_transformation.py --input your-file.xml        # your file
python3 test_transformation.py --input f.xml --output r.xml # test + save
```

---

## Known Limitations

See the [Known Limitations](docs/mapping-notes.md#known-limitations) section of the mapping notes —
notably: individual-name splitting is heuristic (prefer `"Surname, Given"` source data), and
`dataTable` / `methods` / `project` have no ISO 19139 equivalent and are never emitted.

---

## See Also

- [ISO 19139 schema (OGC)](http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd)
- [EML 2.2.0 specification](https://eml.ecoinformatics.org/)
- [Transformation diagram](docs/transformation-diagram.svg)
- [Field mapping reference](docs/mapping-notes.md)
- [Repository README](../../README.md)
