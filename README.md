# LifeWatch XSLT Transformations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![XSLT 1.0](https://img.shields.io/badge/XSLT-1.0-blue.svg)](https://www.w3.org/TR/xslt)

A centralised, authoritative repository of XSLT stylesheets used by the LifeWatch ERIC infrastructure to transform biodiversity metadata between formats and versions.

---

## Repository Structure

```
lifewatch-xslt-transformations/
│
├── transformations/                      # One sub-folder per transformation
│   ├── EML211_to_EML220/                 # EML 2.1.1 → EML 2.2.0
│   ├── EML220_to_DataCite401/            # EML 2.2.0 → DataCite 4.0.1 / OpenAIRE
│   ├── ISO19139_to_EML220/               # ISO 19139 → EML 2.2.0
│   ├── ISO19139_to_EOSC/                 # ISO 19139 → EOSC Resource "Service" (JSON)
│   └── ISO19139_to_DataCite401/          # ISO 19139 → DataCite 4.0.1 / OpenAIRE (Workflow, VRE)
│
│   Every transformation folder follows the same shape:
│
│   <Name>/
│   ├── xslt/
│   │   └── main.xsl                      # Transformation logic (XSLT 1.0)
│   ├── examples/
│   │   ├── input/                        # Representative source sample(s)
│   │   └── output/                       # Expected result(s)
│   ├── docs/
│   │   ├── mapping-notes.md              # Field-level mapping documentation
│   │   └── transformation-diagram.svg    # Visual flow diagram (open in browser)
│   ├── run.py                            # One-command transform + test runner
│   ├── test_transformation.py            # Automated test suite
│   └── README.md
│
│   `ISO19139_to_EOSC` additionally ships `docs/eosc-schema/` (the real EOSC JSON
│   Schemas, vendored locally) and `validate_output.py`, which checks its output
│   against them directly rather than just against worked spreadsheet examples.
│
├── shared/                               # Reusable templates imported by multiple transformations
│   ├── namespaces.xml                    # Canonical namespace declarations
│   └── macros.xsl                        # Common named templates (string-replace, date-normalise, …)
│
├── docs/                                 # Repository-level governance and guides
│   ├── architecture.md                   # Design decisions and diagram
│   ├── contributing.md                   # Branching and review guidelines
│   └── adding-a-transformation.md        # Step by step guide for new transformations
│
├── ci/
│   └── validate.sh                       # CI helper: runs Saxon on every example pair
│
├── LICENSE
└── README.md                             ← you are here
```

---

## Supported Transformations

| Transformation | Source | Target | Output | Status |
|---|---|---|---|---|
| [`EML211_to_EML220`](transformations/EML211_to_EML220) | EML 2.1.1 | EML 2.2.0 | XML | ✅ Stable |
| [`EML220_to_DataCite401`](transformations/EML220_to_DataCite401) | EML 2.2.0 | DataCite 4.0.1 / OpenAIRE (`oaire:resource`) | XML | ✅ Stable |
| [`ISO19139_to_EML220`](transformations/ISO19139_to_EML220) | ISO 19139 | EML 2.2.0 | XML | ✅ Stable |
| [`ISO19139_to_EOSC`](transformations/ISO19139_to_EOSC) | ISO 19139 | EOSC Resource `Service` | JSON | 🚧 In progress — mapping complete, output validated against the real EOSC JSON Schema ([details](transformations/ISO19139_to_EOSC/README.md)) |
| [`ISO19139_to_DataCite401`](transformations/ISO19139_to_DataCite401) | ISO 19139 | DataCite 4.0.1 / OpenAIRE (`Workflow`, `VRE`) | XML | 🚧 In progress — mapping complete, core fields implemented ([details](transformations/ISO19139_to_DataCite401/README.md)) |

Each transformation's own README documents its parameters, known limitations, and
exactly which fields are mapped vs. intentionally left out — read it before relying
on a "🚧 In progress" transformation for anything beyond a first pass.

---

## Transformation Chains

Several transformations share a source or target format and can be composed:

```
EML 2.1.1 ──[EML211_to_EML220]──► EML 2.2.0 ──[EML220_to_DataCite401]──► DataCite 4.0.1
                                       ▲
ISO 19139 ──[ISO19139_to_EML220]──────┘

ISO 19139 ──[ISO19139_to_EOSC]────────► EOSC Resource "Service" (JSON)

ISO 19139 ──[ISO19139_to_DataCite401]─► DataCite 4.0.1 / OpenAIRE (Workflow, VRE)
```

`ISO19139_to_DataCite401` is a **direct** route for `Workflow` / `VRE` resources —
distinct from chaining `ISO19139_to_EML220` → `EML220_to_DataCite401`, which targets
`Dataset` resources and produces a different `resourceType`. Pick the route that
matches the EOSC/OpenAIRE resource type of the record you're converting.

---

## Quick Start

### Prerequisites

- **Python 3.9+** with `pip install lxml` — the primary, recommended way to run and
  test every transformation (`run.py` / `test_transformation.py`, present in every
  `transformations/<Name>/` folder)
- [Saxon-HE](https://www.saxonica.com/download/download_page.xml) (9.x or later) **or**
  any XSLT 1.0-compliant processor, plus Java 8+ — used by `ci/validate.sh` and for
  running a stylesheet directly from the command line

### Run + test a transformation (recommended)

```bash
cd transformations/ISO19139_to_EML220
python3 run.py                              # transforms every examples/input/ file, runs tests
python3 test_transformation.py --input your-file.xml
```

Every transformation folder works the same way — see its own README for
transformation-specific flags (e.g. `--resource-type` on `ISO19139_to_DataCite401`,
`--service-category` on `ISO19139_to_EOSC`). `ISO19139_to_EOSC` additionally ships
`validate_output.py`, which checks its JSON output against the real vendored EOSC
JSON Schema:

```bash
cd transformations/ISO19139_to_EOSC
python3 validate_output.py examples/output/*.json
```

### Run a transformation directly with Saxon

```bash
java -jar saxon-he.jar \
  -s:transformations/EML211_to_EML220/examples/input/sample.xml \
  -xsl:transformations/EML211_to_EML220/xslt/main.xsl \
  -o:output.xml
```

### Run all validation examples

```bash
bash ci/validate.sh
```

The script iterates over every `examples/input/` file, applies the corresponding
stylesheet, and diffs the result against the expected `examples/output/` file. It's
XML-oriented: transformations whose output is JSON (`ISO19139_to_EOSC`) won't get a
meaningful diff from it — use that transformation's own `run.py` /
`test_transformation.py` / `validate_output.py` instead.

---

## Adding a New Transformation

See **[docs/adding-a-transformation.md](docs/adding-a-transformation.md)** for the full checklist.

---

## Governance & Access

| Scope | Visibility |
|---|---|
| This repository (all transformations) | **Private** (current default) |
| Individual stable transformations | Can be split into public repositories when approved |

---

## Contributing

Pull requests are welcome. Please read [docs/contributing.md](docs/contributing.md) before opening one.

---

## License

This project is released under the [MIT License](LICENSE).
© LifeWatch ERIC
