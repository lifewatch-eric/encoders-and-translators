# Mapping Notes — EML 2.1.1 → EML 2.2.0

This document describes every field-level decision made in `xslt/main.xsl`.

---

## 1. Namespace and Schema Location Updates

### 1.1 Root namespace

| Source | Target |
|---|---|
| `eml://ecoinformatics.org/eml-2.1.1` | `https://eml.ecoinformatics.org/eml-2.2.0` |

The root element is reconstructed as `<eml:eml>` bound to the EML 2.2.0 namespace URI. All attributes on the source root are iterated and rewritten where necessary.

### 1.2 `xsi:schemaLocation`

The `xsi:schemaLocation` attribute may contain both the EML namespace URI and the StMML URI. Both are replaced in a single two-pass string-replace chain:

| Find | Replace with |
|---|---|
| `eml://ecoinformatics.org/eml-2.1.1` | `eml://ecoinformatics.org/eml-2.2.0` |
| `http://www.xml-cml.org/schema/stmml-1.1` | `http://www.xml-cml.org/schema/stmml-1.2` |

> **Implementation note:** XSLT 1.0 has no built-in `replace()` function; a recursive named template `replace-string` is used instead (see `shared/macros.xsl` for the shared version).

---

## 2. `packageId` Attribute

The stylesheet accepts a parameter `package-id` (default value `'newID'`).

| Condition | Behaviour |
|---|---|
| Parameter not supplied (or equals `'newID'`) | Existing `packageId` value is preserved unchanged |
| Parameter supplied with a custom value | `packageId` is overwritten with the supplied value |

---

## 3. `<dataset>` Enrichment

### 3.1 `<alternateIdentifier>` injection

EML 2.2.0 requires `<alternateIdentifier>` to appear before other `<dataset>` children. The stylesheet inserts an **empty** `<alternateIdentifier/>` as the very first child of `<dataset>`. Downstream pipelines are expected to populate this with a persistent identifier (e.g. a DOI).

### 3.2 `<distribution>` harvest

A new `<distribution>` element is assembled by collecting `<online>` blocks from two locations in the source document:

| Source XPath | Harvested fields |
|---|---|
| `//additionalMetadata/metadata/gbif/physical` | `objectName` → `<onlineDescription>`, `distribution/online/url` → `<url>` |
| `//dataset/otherEntity/physical` | same as above |

Both sets of `<online>` blocks are placed as siblings inside the single `<distribution>` element.

---

## 4. `<pubDate>` Normalisation

EML 2.2.0 requires dates in ISO 8601 format (`YYYY-MM-DD`). Many EML 2.1.1 records store only a four-digit year.

| Source value | Output value |
|---|---|
| `2019` (year only — no `-` character) | `2019-01-01` |
| `2019-07-15` (already ISO 8601) | `2019-07-15` (unchanged) |

The detection heuristic checks for the presence of a hyphen (`-`) in the string value.

---

## 5. `<dataTable>` Passthrough

`<dataTable>` elements are copied with a guard: if `<attributeList>/<attribute>` children are present, each attribute is reshaped to ensure `<attributeDefinition>` is populated. If no attribute list exists, the element is copied as-is.

---

## 6. `<project>` Normalisation

The EML 2.2.0 `<project>` content model requires `<title>` and `<personnel>` in a specific order.

| Operation | Detail |
|---|---|
| `<title>` | Only the first `<title>` child is emitted (EML 2.2.0 allows only one) |
| `<personnel>/<organizationName>` | Set to `"Not available"` when absent in the source |
| `<personnel>/<positionName>` | Populated from `<role>`; falls back to `"Not available"` when empty |

---

## 7. `<methods>` and `<sampling>` Normalisation

### 7.1 Method steps

Each `<methodStep>` is reconstructed, collecting:
- `<description>/<para>` values, joined with a space separator
- `<instrumentation>/<instrument>` elements
- `<software>/<title>` and `<software>/<version>`

### 7.2 Sampling

`<studyExtent>/<description>/<para>` and `<samplingDescription>/<para>` are extracted and re-wrapped under the EML 2.2.0-compliant structure.

---

## 8. Identity Copy (Catch-All)

All nodes not matched by a more specific template are handled by the identity copy template:

```xml
<xsl:template match="*">
  <xsl:element name="{name(.)}" namespace="{namespace-uri(.)}">
    <xsl:copy-of select="@*"/>
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>
```

This preserves namespace-qualified element names and all attributes without modification.

---

## 9. Shared Utilities

### `replace-string` (named template)

A recursive XSLT 1.0 implementation of string replacement. Accepts `$text`, `$replace`, and `$with` parameters. Used for namespace URI rewriting. The canonical version lives in `shared/macros.xsl`.

### `get-full-path` (mode template)

Builds a slash-separated XPath string from the root to the current node. Useful for debugging and error reporting. Not invoked in the main transformation flow.

---

## 10. Explicitly Out of Scope

The following EML 2.1.1 → 2.2.0 changes are **not** handled by this stylesheet and may require manual intervention:

| Change | Reason not automated |
|---|---|
| `<access>` element removal from within modules | Not present in LifeWatch source data |
| New `<annotation>` elements | No source data to map from |
| `<unitList>` → `<unitDictionary>` rename | Not present in LifeWatch source data |

---

*Last updated: 2026-02-22 — LifeWatch ERIC Service Centre*
