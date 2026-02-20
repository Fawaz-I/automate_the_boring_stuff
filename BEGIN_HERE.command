#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "Python 3 is required" message "Install Python 3 first, then run BEGIN_HERE.command again." as critical'
  exit 1
fi

python3 "$SCRIPT_DIR/build_offline_bundle.py"

if command -v open >/dev/null 2>&1; then
  open "$SCRIPT_DIR/offline_content/index.html"
fi
