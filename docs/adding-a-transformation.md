# Adding a New Transformation

Follow this checklist every time you add a new source-to-target transformation.

---

## 1. Create the folder structure

```bash
NAME=MySource_to_MyTarget   # e.g. EML220_to_DataCite401

mkdir -p transformations/$NAME/{xslt,examples/{input,output},docs}
```

## 2. Write the stylesheet

Create `transformations/$NAME/xslt/main.xsl`.

Include a header comment:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
  transformations/MySource_to_MyTarget/xslt/main.xsl
  ====================================================
  Transforms <source format> to <target format>.

  Parameters:
    (list any xsl:param elements here)

  Author:  <your name> <email>
  Version: 1.0.0
  Date:    YYYY-MM-DD
-->
```

Import shared macros if you need `replace-string` or `normalize-date`:

```xml
<xsl:import href="../../shared/macros.xsl"/>
```

## 3. Add example files

- `examples/input/sample.xml` — a minimal but representative source document
- `examples/output/sample.xml` — the exact expected output after transformation

Run `ci/validate.sh $NAME` to confirm the stylesheet produces the expected output.

## 4. Write the mapping notes

Create `transformations/$NAME/docs/mapping-notes.md` documenting:
- Every source field and its target mapping
- Fields that are dropped and why
- Default values inserted when source is absent
- Any known limitations

## 5. Write the README

Copy the template below into `transformations/$NAME/README.md` and fill in every section.

```markdown
# <Source> → <Target>

## Overview
| Property | Value |
|---|---|
| Source format | ... |
| Target format | ... |
| XSLT version | 1.0 |
| Status | 🚧 In progress / ✅ Stable |

## Transformation Logic
...

## Usage
...

## Testing
...

## Known Limitations
...
```

## 6. Open a pull request

Follow the checklist in [contributing.md](contributing.md).
