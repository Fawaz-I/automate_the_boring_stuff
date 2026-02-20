#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH."
  exit 1
fi

echo "Building offline content..."
python3 "$SCRIPT_DIR/build_offline_bundle.py"

echo
echo "Done. Open this file in your browser:"
echo "  $SCRIPT_DIR/offline_content/index.html"
