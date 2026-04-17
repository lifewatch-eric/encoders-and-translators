# Architecture

This document explains the structural and governance decisions behind the repository.

---

## Design Goals

1. **Single source of truth** — all LifeWatch XSLT transformations live in one repository, eliminating drift between the fragmented GitLab / GitHub repositories that existed before.
2. **Discoverable structure** — a developer landing on any transformation folder immediately understands inputs, outputs, parameters, and edge cases without reading source code.
3. **Testable** — every transformation ships with example input/output pairs and a CI script so regressions are caught before merge.
4. **Extensible** — adding a new transformation is a matter of following the checklist in `adding-a-transformation.md`; no changes to shared infrastructure are required.
5. **Flexible visibility** — the repository is private by default; individual stable transformations can be extracted into standalone public repositories when governance approves.

---

## Transformation Flow (Logical)

```
EML 2.1.1 ──────────────────────────────────► EML 2.2.0
                EML211_to_EML220/xslt/main.xsl


EML 2.2.0 ──────────────────────────────────► DataCite 4.0.1
                EML220_to_DataCite401/xslt/main.xsl
```

Transformations can be chained:

```
EML 2.1.1  ──[EML211_to_EML220]──►  EML 2.2.0  ──[EML220_to_DataCite401]──►  DataCite 4.0.1
```

---

## Repository Layout Rationale

### `transformations/<Name>/`

Each transformation is fully self-contained. This enables:
- Independent versioning via Git tags (`EML211_to_EML220/v1.2.0`)
- Extraction into a public repository with a single `git subtree` command
- Clear ownership assignment per transformation

### `shared/`

Named templates that appear in more than one transformation (e.g. `replace-string`, `normalize-date`) are promoted to `shared/macros.xsl`. Transformations import this file rather than duplicating logic.

### `docs/`

Repository-level documentation that spans all transformations: governance, contributing guide, and this architecture document.

### `ci/`

The `validate.sh` script is the single entry point for testing. It requires only Java + Saxon and can be run locally or in any CI environment (GitHub Actions, GitLab CI, Jenkins).

---

## Visibility Model

```
lifewatch-xslt-transformations  (PRIVATE — default)
│
├── transformations/
│   ├── EML211_to_EML220/         ← can be extracted → PUBLIC repo
│   ├── EML220_to_DataCite401/    ← can be extracted → PUBLIC repo
│   └── ISO19139_to_EML220/       ← can be extracted → PUBLIC repo
│
└── shared/                       ← stays PRIVATE (internal utility)
```

To extract a transformation as a public repository:

```bash
git subtree split --prefix=transformations/EML211_to_EML220 -b split-eml211
git push https://github.com/lifewatch/EML211_to_EML220.git split-eml211:main
```

---

## Future Transformations

Planned additions (not yet implemented):

| Transformation | Priority |
|---|---|
| `EML220_to_DataCite401` | High |
| `ISO19139_to_EML220` | High |
| `EML220_to_DublinCore` | Medium |
| `DwC_to_EML220` | Low |
