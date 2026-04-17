#!/usr/bin/env bash
# ==============================================================================
# ci/validate.sh
# ==============================================================================
# Validate all (or a single) XSLT transformation by running Saxon against every
# example input and diffing the result against the expected output.
#
# Usage:
#   bash ci/validate.sh                      # validate all transformations
#   bash ci/validate.sh EML211_to_EML220     # validate one transformation
#
# Requirements:
#   - Java 8+
#   - Saxon-HE JAR accessible via SAXON_JAR env variable or on the PATH
#     (default search: ./saxon-he.jar, ~/saxon-he.jar)
#   - xmllint (optional — used for whitespace normalisation before diff)
# ==============================================================================

set -euo pipefail

# ── Colour output ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No colour

# ── Locate Saxon ───────────────────────────────────────────────────────────────
SAXON_JAR="${SAXON_JAR:-}"
if [[ -z "$SAXON_JAR" ]]; then
  for candidate in ./saxon-he.jar ~/saxon-he.jar /usr/local/lib/saxon-he.jar; do
    if [[ -f "$candidate" ]]; then
      SAXON_JAR="$candidate"
      break
    fi
  done
fi

if [[ -z "$SAXON_JAR" ]]; then
  echo -e "${RED}ERROR: Saxon JAR not found.${NC}"
  echo "Set the SAXON_JAR environment variable to the path of your Saxon-HE JAR."
  echo "  e.g.  export SAXON_JAR=/opt/saxon/saxon-he-12.4.jar"
  exit 1
fi

# ── Discover transformations ───────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILTER="${1:-}"

if [[ -n "$FILTER" ]]; then
  TRANSFORMATIONS=("$REPO_ROOT/transformations/$FILTER")
else
  mapfile -t TRANSFORMATIONS < <(find "$REPO_ROOT/transformations" -mindepth 1 -maxdepth 1 -type d | sort)
fi

PASS=0
FAIL=0
SKIP=0

# ── Run validations ────────────────────────────────────────────────────────────
for TRANS_DIR in "${TRANSFORMATIONS[@]}"; do
  TRANS_NAME="$(basename "$TRANS_DIR")"
  XSL="$TRANS_DIR/xslt/main.xsl"
  INPUT_DIR="$TRANS_DIR/examples/input"
  EXPECTED_DIR="$TRANS_DIR/examples/output"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Transformation: $TRANS_NAME"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ ! -f "$XSL" ]]; then
    echo -e "  ${YELLOW}SKIP${NC}  — no main.xsl found at $XSL"
    ((SKIP++))
    continue
  fi

  if [[ ! -d "$INPUT_DIR" ]]; then
    echo -e "  ${YELLOW}SKIP${NC}  — no examples/input directory"
    ((SKIP++))
    continue
  fi

  for INPUT_FILE in "$INPUT_DIR"/*.xml; do
    [[ -f "$INPUT_FILE" ]] || continue
    BASENAME="$(basename "$INPUT_FILE")"
    # Derive expected output filename by replacing the first part of the name
    EXPECTED_FILE="$EXPECTED_DIR/${BASENAME/input/output}"
    # Fallback: same filename in output dir
    if [[ ! -f "$EXPECTED_FILE" ]]; then
      EXPECTED_FILE="$EXPECTED_DIR/$BASENAME"
    fi

    ACTUAL_TMP="$(mktemp /tmp/validate_actual_XXXXXX.xml)"
    trap 'rm -f "$ACTUAL_TMP"' EXIT

    echo -n "  Testing $BASENAME ... "

    # Run Saxon
    if ! java -jar "$SAXON_JAR" -s:"$INPUT_FILE" -xsl:"$XSL" -o:"$ACTUAL_TMP" 2>/tmp/saxon_stderr; then
      echo -e "${RED}FAIL${NC}  (Saxon error)"
      cat /tmp/saxon_stderr | sed 's/^/    /'
      ((FAIL++))
      continue
    fi

    if [[ ! -f "$EXPECTED_FILE" ]]; then
      echo -e "${YELLOW}WARN${NC}  (no expected output file at $EXPECTED_FILE — skipping diff)"
      ((SKIP++))
      continue
    fi

    # Normalise and diff
    if command -v xmllint &>/dev/null; then
      NORM_ACTUAL="$(xmllint --c14n "$ACTUAL_TMP" 2>/dev/null)"
      NORM_EXPECTED="$(xmllint --c14n "$EXPECTED_FILE" 2>/dev/null)"
    else
      NORM_ACTUAL="$(cat "$ACTUAL_TMP")"
      NORM_EXPECTED="$(cat "$EXPECTED_FILE")"
    fi

    if [[ "$NORM_ACTUAL" == "$NORM_EXPECTED" ]]; then
      echo -e "${GREEN}PASS${NC}"
      ((PASS++))
    else
      echo -e "${RED}FAIL${NC}  (output differs from expected)"
      diff <(echo "$NORM_EXPECTED") <(echo "$NORM_ACTUAL") | head -40 | sed 's/^/    /'
      ((FAIL++))
    fi

    rm -f "$ACTUAL_TMP"
    trap - EXIT
  done
done

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════"
echo "  Results:  ${GREEN}PASS $PASS${NC}  |  ${RED}FAIL $FAIL${NC}  |  ${YELLOW}SKIP $SKIP${NC}"
echo "══════════════════════════════════════════════════"

[[ "$FAIL" -eq 0 ]]
