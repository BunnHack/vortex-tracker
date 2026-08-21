#!/usr/bin/env bash
# Vortex Client Tracker — one-shot fetch → store → analyze → diff → commit.
set -u
# only run when executed, never when sourced (keeps cwd safe)
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  : # execute below
else
  echo "do not source me; run directly" >&2; return 0
fi
cd "$(dirname "$0")/.."
mkdir -p reports snapshots
[ -d .git ] || echo "warning: not a git repo (commit step will no-op)"
BASE="https://playvortex.io"
DL="$BASE/download/windows"
CACHE="$HOME/.cache/vortex-tracker"
mkdir -p "$CACHE"

getver() {
python3 - <<'PY' 2>/dev/null || echo __SHA__
import json,urllib.request
try:
    print(json.load(urllib.request.urlopen('https://playvortex.io/api/studio-version',timeout=20)).get('version','__SHA__'))
except Exception:
    print('__SHA__')
PY
}

# render a filename-safe version tag: probe value, else first 8 of extracted sha
verfile() {
  local v="$1"
  if [ "$v" = "__SHA__" ]; then
    v=$(python3 -c "import hashlib;print(hashlib.sha256(open('exe_current.bin','rb').read()).hexdigest()[:8])")
  fi
  echo "$v"
}

dl() {
python3 - "$DL" "$CACHE/Vortex-Windows.zip" <<'PY'
import sys,urllib.request
req=urllib.request.Request(sys.argv[1], headers={'User-Agent':'Mozilla/5.0'})
open(sys.argv[2],'wb').write(urllib.request.urlopen(req,timeout=300).read())
print("downloaded", sys.argv[2])
PY
}

echo "[1] version probe:"; VER=$(getver); echo "    $VER"
echo "[2] downloading $DL"
dl
echo "[3] extracting exe"
python3 - "$CACHE/Vortex-Windows.zip" <<'PY'
import sys,zipfile
z=zipfile.ZipFile(sys.argv[1])
for n in z.namelist():
    if n.lower().endswith('.exe'):
        b=z.read(n)
        open('exe_current.bin','wb').write(b)
        print("   extracted", n, len(b)); break
else:
    sys.exit("no exe")
PY
echo "[4] analyzing"
python3 bin/analyze.py < exe_current.bin > "reports/latest.json"
VERFILE=$(verfile "$VER")
cp "reports/latest.json" "snapshots/${VERFILE}.json"
echo "[5] diff"
python3 bin/diff.py "reports/latest.json"
echo "[6] record provenance"
SHA=$(python3 -c "import json;print(json.load(open('reports/latest.json'))['sha256'])")
echo "$(date -Is)  version=${VERFILE}  probe=${VER}  sha256=${SHA}" >> reports/history.log