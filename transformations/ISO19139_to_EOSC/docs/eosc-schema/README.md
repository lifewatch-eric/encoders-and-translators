# Vendored EOSC JSON Schemas

Local copies of the two JSON Schema files this transformation's output must satisfy,
pulled from the [EOSC-PLATFORM/eosc-resources-model](https://github.com/EOSC-PLATFORM/eosc-resources-model)
repository (`schemas/` folder) on 2026-07-14, so `test_transformation.py` can validate
against the real schema without a network dependency.

- `eosc-resource.schema.json` — the base `EOSC Resource` schema (`urn:jsonschema:eosc:eosc-resource`), vendored as-is.
- `service.schema.json` — the `Service` schema (`urn:jsonschema:eosc:service`), **patched**.

## Patch applied to `service.schema.json`

The file as published at
[`schemas/service.schema.json`](https://github.com/EOSC-PLATFORM/eosc-resources-model/blob/main/schemas/service.schema.json)
is **not valid JSON** — it is missing a closing `}` around the
`relatedInteroperabilityGuidelines.items` object, so the file fails to parse
(`json.load` raises `Expecting ',' delimiter: line 140 column 3`). One `}` was added
before `"required": ["webpage", "jurisdiction", "trl"]` to close both
`relatedInteroperabilityGuidelines` and the enclosing `properties` object. No field
names, types, or requirements were changed — this is a syntax-only fix. Worth
reporting upstream.

## Known schema-authoring quirk: `allOf` + `additionalProperties: false`

`service.schema.json` composes `eosc-resource.schema.json` via `allOf`, and **both**
branches declare `"additionalProperties": false`. Under `allOf`, every branch is
validated against the **full** instance independently — so the base-resource branch
sees the service-specific fields (`webpage`, `trl`, `categories`, ...) as "unexpected
additional properties", and the service branch sees the base fields (`name`,
`publishingDate`, `url`, ...) as unexpected in the same way. This is a well-known
JSON Schema anti-pattern (`additionalProperties: false` does not compose across
`allOf`), not a bug in this transformation's output. A single strict `additionalProperties: false`
pass across the merged document will always report these as errors, on **any**
correctly-shaped Service resource — see how `validate_output.py` interprets these
specifically as expected/ignorable versus the errors that are real (unknown fields
not defined in *either* branch, missing genuinely-required fields, wrong types).

## Re-fetching

```bash
curl -s https://raw.githubusercontent.com/EOSC-PLATFORM/eosc-resources-model/main/schemas/eosc-resource.schema.json -o eosc-resource.schema.json
curl -s https://raw.githubusercontent.com/EOSC-PLATFORM/eosc-resources-model/main/schemas/service.schema.json -o service.schema.json
# then re-apply the brace patch above if the upstream bug hasn't been fixed yet
```
