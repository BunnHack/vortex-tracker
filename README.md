# Vortex Client Tracker

Automatically fetch, unpack, and diff Vortex desktop binaries — so you can
see what a release **leaked, changed, or removed** without running rizin by hand.

Modeled on the Roblox Client Tracker playbook: watch the distribution endpoint,
snapshot key internals, commit the diff, let changes surface themselves.

## What it does

1. **Version probe** — `GET /api/studio-version` -> live build tag.
2. **Download** — `GET /download/windows` (Vortex-Windows.zip) => `Vortex/Vortex.exe`.
3. **Extract** the PE.
4. **Analyze** — a string/constant pass mirroring a manual rizin walk:
   - `endpoints` — `/api/*`, `/releases-*`, `/download/*` paths
   - `env_toggles` — `VORTEX_*`, `WGPU_*`, backend/stage/instance/token switches
   - `build_paths` — leaked filesystem roots (`/private/tmp/…`, `/Users/…/.cargo`, …)
   - `struct_defs` — every `struct … with N elements` serde schema (project-file + network contracts)
   - `tokens` — credential-ish literals (`X-App-Token`, `pp_token`, …)
5. **Diff** — compare against the newest saved snapshot; emit ADDED/REMOVED.
6. **Commit** — if changed, `git` records the new snapshot + history line.

## Usage

```bash
bin/track.sh                 # full run: probe→download→analyze→diff
python3 bin/analyze.py < exe > out.json      # analyze any Vortex.exe
python3 bin/diff.py reports/<ver>.json       # diff vs last snapshot
```

## Automation

A **GitHub Actions workflow** (`.github/workflows/track.yml`) runs the tracker
for you:

- **scheduled** every day 06:00 UTC
- **manual** via the Actions → *vortex-tracker* → *Run workflow* button

It fetches, unpacks, analyzes, diffs, and — if anything changed — commits the
new snapshot and pushes it back to this repo. No cron, no local machine, no
touching binaries by hand; the snapshot + `reports/history.log` accumulate as
commits so the leak history is the git history.

## Layout

```
bin/analyze.py     PE → JSON snapshot (endpoints, toggles, paths, structs, tokens)
bin/diff.py        ADDED / REMOVED vs newest saved snapshot
bin/track.sh       end-to-end run
reports/<ver>.json analyzed snapshot per version
snapshots/<ver>.json    committed snapshot (diff baseline)
exe_current.bin    last extracted binary (gitignored)
```

## Notes

- This is a read-only monitoring tool. It downloads Vortex's own publicly hosted
  installer, runs no code, and only reads strings off the PE header/footer.
- `exe_current.bin` and the zip are `gitignore`d (large); only the 1-2 KB JSON
  snapshots are committed, so the repo stays small and diff-friendly.