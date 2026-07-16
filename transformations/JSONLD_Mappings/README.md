# JSON-LD Mappings

LifeWatch ERIC metadata → **schema.org JSON-LD**, implemented as self-contained
Google Colab notebooks rather than XSLT stylesheets.

---

## Why this folder is different

Every other folder under `transformations/` is an **XSLT 1.0 stylesheet** with a
`run.py` / `test_transformation.py` harness (see the [repository
README](../../README.md)). The two mappings here target **JSON-LD** (schema.org
vocabulary) instead of another XML dialect or a REST-API JSON model, and are
implemented as **Python notebooks** designed to run interactively in Google Colab:
each installs its own dependencies on first run, prompts for a file upload,
converts, validates, and downloads the result. There's no local CLI runner for
these (yet) — see each sub-folder's README for exact usage.

---

## Contents

| Mapping | Source | Target `@type` | Version | Notebook |
|---|---|---|---|---|
| [`EML_to_JSONLD`](EML_to_JSONLD) | EML 2.2.0 | `Dataset` | 5.2 | `EML_to_JsonLD_v2_NEW-v5.2.ipynb` |
| [`ISO19139_to_JSONLD`](ISO19139_to_JSONLD) | ISO 19139 | auto-detected: `CreativeWork`, `Action`, or `HowTo` | 2.1 | `ISO19139_to_JsonLD_v2.1.ipynb` |

Together these two cover every resource type in the LifeWatch ERIC catalogue:
Datasets (EML) on one side; Workflows, VREs, and Services (ISO 19139) on the other.
Both target the same `{"@vocab": "https://schema.org/"}` JSON-LD context and share
conventions — hardcoded `provider` block for LifeWatch ERIC, the same
`@id`/`url`/`sameAs` identifier strategy, the same `OK` / `PARTIAL` / `LOST` (/
`DROPPED`) mapping-report status codes — documented in full in each sub-folder's
PDF.

---

## File Structure

```
JSONLD_Mappings/
├── EML_to_JSONLD/
│   ├── EML_to_JsonLD_v2_NEW-v5.2.ipynb
│   ├── docs/
│   │   └── EML_to_JsonLD_Documentation_v5.2.pdf
│   └── README.md
├── ISO19139_to_JSONLD/
│   ├── ISO19139_to_JsonLD_v2.1.ipynb
│   ├── docs/
│   │   └── ISO19139_to_JsonLD_Documentation_v2.1.pdf
│   └── README.md
└── README.md                          ← this file
```

---

## Relationship to the other transformations

`ISO19139_to_JSONLD` and [`ISO19139_to_EOSC`](../ISO19139_to_EOSC) both start from
ISO 19139 but target different systems — schema.org JSON-LD (for general web/search
discovery) versus the EOSC resources model (for EOSC Beyond onboarding). They are
independent, parallel mappings from the same source format, not a chain.

---

## See Also

- [Repository README](../../README.md)
- [schema.org validator](https://validator.schema.org/)
