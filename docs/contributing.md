# Contributing Guide

Thank you for contributing to the LifeWatch XSLT Transformations repository.

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, reviewed code only |
| `dev` | Integration branch for ongoing work |
| `feat/<name>` | New transformation or significant feature |
| `fix/<name>` | Bug fix on an existing transformation |
| `docs/<name>` | Documentation-only change |

All work is done on a feature or fix branch and merged into `dev` via a pull request. `dev` is merged into `main` after review.

---

## Adding a New Transformation

Follow the checklist in [adding-a-transformation.md](adding-a-transformation.md).

---

## Pull Request Checklist

Before opening a PR, confirm:

- [ ] The transformation folder follows the standard structure (see `adding-a-transformation.md`)
- [ ] `xslt/main.xsl` is valid XSLT 1.0 and passes `xmllint --noout`
- [ ] At least one `examples/input/*.xml` and matching `examples/output/*.xml` are included
- [ ] `ci/validate.sh <TransformationName>` exits with code 0
- [ ] `docs/mapping-notes.md` documents every non-trivial mapping decision
- [ ] The transformation `README.md` is complete (usage, parameters, known limitations)
- [ ] `CHANGELOG.md` entry is added if this modifies an existing transformation

---

## Extracting a Transformation into a Public Repository

1. Obtain governance approval.
2. Run:
   ```bash
   git subtree split --prefix=transformations/<Name> -b split-<name>
   git push https://github.com/lifewatch/<Name>.git split-<name>:main
   ```
3. Add the public URL to the table in the root `README.md`.
4. Keep the transformation folder in this repository as the canonical source; the public repo is a read-only mirror updated on each tagged release.

---

## Code Style

- Indent with **2 spaces** in XSLT files.
- Add a comment block at the top of every `main.xsl` describing purpose, author, and version.
- Use named templates for any logic longer than 10 lines.
- Prefer `<xsl:element>` + `<xsl:attribute>` over literal result elements when the namespace may vary.
