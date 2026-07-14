# LifeWatch XSLT Transformations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![XSLT 1.0](https://img.shields.io/badge/XSLT-1.0-blue.svg)](https://www.w3.org/TR/xslt)

A centralised, authoritative repository of XSLT stylesheets used by the LifeWatch ERIC infrastructure to transform biodiversity metadata between formats and versions.

---

## Repository Structure

```
lifewatch-xslt-transformations/
│
├── transformations/                  # One sub-folder per transformation
│   ├── EML211_to_EML220/             # EML 2.1.1 → EML 2.2.0
│   │   ├── xslt/
│   │   │   └── main.xsl             # Default transformation logic
│   │   ├── examples/
│   │   │   ├── input/               # Representative EML 2.1.1 sample(s)
│   │   │   └── output/              # Expected EML 2.2.0 result(s)
│   │   ├── docs/
│   │   │   └── mapping-notes.md     # Field-level mapping documentation
│   │   └── README.md
│   │
│   ├── EML220_to_DataCite401/        # EML 2.2.0 → DataCite 4.0.1
│   │   ├── xslt/
│   │   │   └── main.xsl
│   │   ├── examples/
│   │   │   ├── input/
│   │   │   └── output/
│   │   ├── docs/
│   │   │   └── mapping-notes.md
│   │   └── README.md
│   │
│   ├── ISO19139_to_EML220/           # ISO 19139 → EML 2.2.0
│   │   ├── xslt/
│   │   │   └── main.xsl
│   │   ├── examples/
│   │   │   ├── input/
│   │   │   └── output/
│   │   ├── docs/
│   │   │   └── mapping-notes.md
│   │   └── README.md
│   │
│   ├── ISO19139_to_EOSC/             # ISO 19139 → EOSC Resource "Service" (JSON)
│   │   ├── xslt/
│   │   │   └── main.xsl
│   │   ├── examples/
│   │   │   ├── input/
│   │   │   └── output/
│   │   ├── docs/
│   │   │   └── mapping-notes.md
│   │   └── README.md
│   │
│   └── ISO19139_to_DataCite401/      # ISO 19139 → DataCite 4.0.1 (OpenAIRE), Workflow / VRE
│       ├── xslt/
│       │   └── main.xsl
│       ├── examples/
│       │   ├── input/
│       │   └── output/
│       ├── docs/
│       │   └── mapping-notes.md
│       └── README.md
│
├── shared/                           # Reusable templates imported by multiple transformations
│   ├── namespaces.xml                # Canonical namespace declarations
│   └── macros.xsl                   # Common named templates (string-replace, date-normalise, …)
│
├── docs/                             # Repository-level governance and guides
│   ├── architecture.md              # Design decisions and diagram
│   ├── contributing.md              # Branching and review guidelines
│   └── adding-a-transformation.md   # Step by step guide for new transformations
│
├── ci/
│   └── validate.sh                  # CI helper: runs Saxon on every example pair
│
├── LICENSE
└── README.md                        ← you are here
```

---

## Supported Transformations

| Transformation | Source Format | Target Format | XSLT Version | Status |
|---|---|---|---|---|
| `EML211_to_EML220` | EML 2.1.1 | EML 2.2.0 | 1.0 | ✅ Stable |
| `EML220_to_DataCite401` | EML 2.2.0 | DataCite 4.0.1 | 1.0 | ✅ Stable|
| `ISO19139_to_EML220` | ISO 19139 | EML 2.2.0 | 1.0 | 🚧 Planned |
| [`ISO19139_to_EOSC`](transformations/ISO19139_to_EOSC) | ISO 19139 | EOSC Resource "Service" (JSON) | 1.0 | 🚧 In progress — mapping done, core fields implemented ([details](transformations/ISO19139_to_EOSC/README.md)) |
| [`ISO19139_to_DataCite401`](transformations/ISO19139_to_DataCite401) | ISO 19139 | DataCite 4.0.1 / OpenAIRE (`Workflow`, `VRE`) | 1.0 | 🚧 In progress — mapping done, core fields implemented ([details](transformations/ISO19139_to_DataCite401/README.md)) |

---

## Quick Start

### Prerequisites

- [Saxon-HE](https://www.saxonica.com/download/download_page.xml) (9.x or later) **or** any XSLT 1.0-compliant processor
- Java 8+ (required by Saxon)

### Run a transformation

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

The script iterates over every `examples/input/` file, applies the corresponding stylesheet, and diffs the result against the expected `examples/output/` file.

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
