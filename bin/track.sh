#!/usr/bin/env bash
# Vortex Client Tracker — one-shot fetch → store → analyze → diff → commit.
set -u
cd "$(dirname "$0")/.."
BASE="https://playvortex.io"
DL="$BASE/download/windows"
CACHE="$HOME/.cache/vortex-tracker"
mkdir -p "$CACHE"

getver() {
python3 - <<'PY' 2>/dev/null || echo ?
import json,urllib.request
try:
    print(json.load(urllib.request.urlopen('https://playvortex.io/api/studio-version',timeout=20)).get('version','?'))
except Exception:
    print('?')
PY
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
python3 bin/analyze.py < exe_current.bin > "reports/${VER}.json"
cp "reports/${VER}.json" "snapshots/${VER}.json"
echo "[5] diff"
python3 bin/diff.py "reports/${VER}.json"
echo "[6] record provenance"
echo "$(date -Is)  version=$VER  sha256=$(python3 -c "import json;print(json.load(open('reports/${VER}.json'))['sha256'])")" >> reports/history.log