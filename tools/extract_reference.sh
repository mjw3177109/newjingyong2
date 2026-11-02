#!/usr/bin/env bash
# Only for private analysis; do not commit decompiled scripts or SWF graphics to the HTML5 output.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
SWF="${1:-jin.swf}"
OUT="${2:-/tmp/jy2-decompiled}"
mkdir -p "$OUT"
python3 tools/inspect_swf.py "$SWF" --out "$OUT/swf_inventory.json"
if [[ -f FFDec/ffdec.jar ]]; then
  echo 'Using checked-in FFDec with Java. If the legacy jar fails, install an updated supported FFDec CLI.'
  java -Djava.awt.headless=true -Xmx2g -jar FFDec/ffdec.jar -cli -export script "$OUT/scripts" "$SWF"
else
  echo 'No FFDec/ffdec.jar found' >&2;exit 2
fi
find "$OUT/scripts" -type f \( -name '*.as' -o -name '*.txt' \) | wc -l | awk '{print "Exported script files:",$1}'
echo "Decompiled scripts remain in $OUT and are NOT committed to the web application."
