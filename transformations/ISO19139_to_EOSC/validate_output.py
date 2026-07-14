#!/usr/bin/env python3
"""
transformations/ISO19139_to_EOSC/validate_output.py
=============================================
Validates a transformed EOSC Service JSON file against the real EOSC
resources model — vendored locally in docs/eosc-schema/ from
https://github.com/EOSC-PLATFORM/eosc-resources-model (schemas/eosc-resource.schema.json
+ schemas/service.schema.json).

Why not just run the two schemas through jsonschema's allOf support directly:
service.schema.json composes eosc-resource.schema.json via allOf, and BOTH
branches declare "additionalProperties": false. Under allOf, every branch is
checked against the FULL instance independently, so each branch flags the
other branch's legitimate fields as "unexpected" — a well-known JSON Schema
authoring anti-pattern (additionalProperties does not compose across allOf).
This script instead merges the two branches' properties/required lists into
one flat schema before validating, which is what "does this object contain
exactly the allowed EOSC Service fields, correctly shaped" actually means.

See docs/eosc-schema/README.md for the vendoring details and the one-line
syntax patch applied to the upstream service.schema.json (which does not
parse as JSON in its published form).

Usage:
    python3 validate_output.py examples/output/semantic-platform-service-eosc-service.json
    python3 validate_output.py examples/output/*.json

Requires: pip install jsonschema referencing
Exit code: 0 if no unexpected errors, 1 otherwise. "id" required and empty
"publicContact" are reported but do not affect the exit code — see
docs/mapping-notes.md, "Validated against the real EOSC schema".
"""

import sys
import json
import argparse
from pathlib import Path

HERE = Path(__file__).parent.resolve()
SCHEMA_DIR = HERE / "docs" / "eosc-schema"

GREEN = "\033[32m"; RED = "\033[31m"; YELLOW = "\033[33m"; BOLD = "\033[1m"; RESET = "\033[0m"

# Errors that are known, documented, and don't block the exit code —
# see docs/mapping-notes.md Known Limitations.
EXPECTED_MESSAGES = {
    "'id' is a required property",
}


def build_merged_schema():
    resource_schema = json.loads((SCHEMA_DIR / "eosc-resource.schema.json").read_text())
    service_schema = json.loads((SCHEMA_DIR / "service.schema.json").read_text())
    service_branch = service_schema["allOf"][1]

    merged = {
        "type": "object",
        "properties": {**resource_schema["properties"], **service_branch["properties"]},
        "required": sorted(set(resource_schema.get("required", [])) | set(service_branch.get("required", []))),
        "additionalProperties": False,
    }
    return merged


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", type=Path)
    args = p.parse_args()

    try:
        import jsonschema
    except ImportError:
        print(f"{YELLOW}jsonschema not installed — skipping schema validation.{RESET}")
        print(f"  Install with: pip install jsonschema")
        sys.exit(0)

    # Draft202012Validator needs jsonschema >= 4.18. The merged schema below
    # only uses keywords supported since Draft 7 (type, properties, required,
    # additionalProperties, format, items) so an older jsonschema install
    # (e.g. 3.2.0, common where other tools pin jsonschema<4) validates it
    # identically via Draft7Validator.
    ValidatorClass = getattr(jsonschema, "Draft202012Validator", jsonschema.Draft7Validator)

    schema = build_merged_schema()
    validator = ValidatorClass(schema)

    overall_ok = True
    for path in args.files:
        data = json.loads(path.read_text())
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        real_errors = [e for e in errors if e.message not in EXPECTED_MESSAGES]
        expected = [e for e in errors if e.message in EXPECTED_MESSAGES]

        print(f"\n{BOLD}{path.name}{RESET}")
        for e in expected:
            print(f"  {YELLOW}⚠  expected{RESET}  {list(e.path)}: {e.message}  (see Known Limitations)")
        if real_errors:
            overall_ok = False
            for e in real_errors:
                print(f"  {RED}✗  {list(e.path)}: {e.message}{RESET}")
        else:
            print(f"  {GREEN}✅  matches the merged EOSC Resource + Service schema{RESET}")

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
