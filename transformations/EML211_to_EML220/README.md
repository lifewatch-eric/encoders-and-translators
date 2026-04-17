# EML 2.1.1 → EML 2.2.0

Upgrades an Ecological Metadata Language document from version **2.1.1** to **2.2.0**.

---

## Overview

| Property | Value |
|---|---|
| Source format | EML 2.1.1 (`eml://ecoinformatics.org/eml-2.1.1`) |
| Target format | EML 2.2.0 (`https://eml.ecoinformatics.org/eml-2.2.0`) |
| XSLT version | 1.0 |
| Stylesheet | `xslt/main.xsl` |
| Status | ✅ Stable |

---

## Transformation Logic

The stylesheet applies the following operations (see [`docs/mapping-notes.md`](docs/mapping-notes.md) for full details):

1. **Namespace update** : replaces `eml://ecoinformatics.org/eml-2.1.1` with `https://eml.ecoinformatics.org/eml-2.2.0` throughout root-level attributes and `xsi:schemaLocation`.
2. **StMML schema update** : replaces `stmml-1.1` references with `stmml-1.2`.
3. **`packageId` override** : accepts an optional `package-id` parameter; if supplied, the root attribute is overwritten with the new value.
4. **`alternateIdentifier` injection** : inserts an empty `<alternateIdentifier/>` element as the first child of `<dataset>` to satisfy the EML 2.2.0 schema.
5. **Distribution harvest** : collects `<online>` distribution blocks from both `additionalMetadata/metadata/gbif/physical` and `dataset/otherEntity/physical` and places them under a top-level `<distribution>` element inside `<dataset>`.
6. **`pubDate` normalisation** : year-only values (e.g. `2019`) are converted to ISO 8601 `YYYY-01-01` format.
7. **`dataTable` passthrough** : `<dataTable>` elements are copied with a defensive guard on `<attributeList>/<attribute>`.
8. **`project` / `methods` / `sampling` normalisation** — personnel roles, method steps, and sampling descriptions are reshaped to match the stricter EML 2.2.0 content model.
9. **Identity copy** : all other nodes are copied recursively preserving namespace and attribute information.

### Transformation Flow

```
EML 2.1.1 document
        │
        ▼
┌───────────────────────────────────┐
│  Match root /*                    │
│  ├─ Rewrite xsi:schemaLocation    │
│  ├─ Update packageId (optional)   │
│  └─ Iterate top-level children    │
│       ├─ <access>     → copy      │
│       ├─ <dataset>    → enrich    │
│       │   ├─ inject <alternateIdentifier/>
│       │   ├─ harvest <distribution>
│       │   ├─ normalise <pubDate>  │
│       │   ├─ reshape <dataTable>  │
│       │   ├─ reshape <project>    │
│       │   └─ reshape <methods>    │
│       ├─ <citation>   → copy      │
│       ├─ <software>   → copy      │
│       └─ <protocol>   → copy      │
└───────────────────────────────────┘
        │
        ▼
EML 2.2.0 document
```

---

## Usage

### Saxon (recommended)

```bash
java -jar saxon-he.jar \
  -s:examples/input/sample-eml211.xml \
  -xsl:xslt/main.xsl \
  -o:output.xml
```

### With a custom `packageId`

```bash
java -jar saxon-he.jar \
  -s:examples/input/sample-eml211.xml \
  -xsl:xslt/main.xsl \
  -o:output.xml \
  package-id=my.new.package.id
```

### xsltproc (XSLT 1.0 only, no parameter support in all versions)

```bash
xsltproc xslt/main.xsl examples/input/sample-eml211.xml > output.xml
```

---

## Testing

Validate that the transformation produces the expected output:

```bash
# From the repository root
bash ci/validate.sh EML211_to_EML220
```

The script applies `main.xsl` to every file in `examples/input/` and compares the result (after normalising whitespace) to the corresponding file in `examples/output/`.

---

## File Structure

```
EML211_to_EML220/
├── xslt/
│   └── main.xsl              ← transformation stylesheet
├── examples/
│   ├── input/
│   │   └── sample-eml211.xml ← representative EML 2.1.1 document
│   └── output/
│       └── sample-eml220.xml ← expected EML 2.2.0 result
├── docs/
│   └── mapping-notes.md      ← field-level mapping documentation
└── README.md                 ← this file
```

---

## Known Limitations

- Written against **XSLT 1.0**; string manipulation relies on recursive named templates rather than `fn:replace`.
- `<alternateIdentifier>` is always injected as empty; downstream systems should populate it with a persistent identifier.
- Year-only `pubDate` values are normalised to `YYYY-01-01`; month precision is not inferred.

---

## See Also

- [EML 2.2.0 specification](https://eml.ecoinformatics.org/)
- [EML 2.1.1 → 2.2.0 migration guide](https://eml.ecoinformatics.org/whats-new-in-eml-2-2-0)
- [Repository-level README](../../README.md)
