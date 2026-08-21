#!/usr/bin/env python3
"""Diff an analyzer report against the newest saved snapshot.
Exit code 0 = no change, 1 = changed."""
import json, sys, os

cur = json.load(open(sys.argv[1]))

priors = sorted(
    f for f in os.listdir("snapshots")
    if f.endswith(".json")
)
baseline = json.load(open(os.path.join("snapshots", priors[-1]))) if priors else None

def show(section, items, tag):
    if not items: return
    print(f"[{section}] {tag} ({len(items)}):")
    for x in sorted(items)[:20]:
        print(f"    {tag}  {str(x)[:90]}")

def toks(v):
    return set(f"{t.get('kw','')}@{t.get('off','')}" for t in v)

if baseline is None:
    print("no prior snapshot — baseline only")
    print("sha256", json.load(open(sys.argv[1]))["sha256"])
    cur = json.load(open(sys.argv[1]))
    for s in ["version_hints","endpoints","env_toggles","build_paths","struct_defs"]:
        print(f"\n{s} ({len(cur[s])}):")
        for x in (cur[s] or [])[:25]:
            print("   ", str(x)[:88])
    print(f"\ntokens ({len(cur['tokens'])}):")
    for t in cur["tokens"][:20]:
        print(f"   {t.get('kw','')} @ {t.get('off','')}: {t.get('ctx','')[:60]}")
    sys.exit(0)

cur = json.load(open(sys.argv[1]))
changed = False
for k in ["version_hints","endpoints","env_toggles","build_paths","struct_defs"]:
    old, new = set(baseline.get(k) or []), set(cur.get(k) or [])
    if old != new:
        changed = True
        show(f"{k} ADDED", new-old, "+")
        show(f"{k} REMOVED", old-new, "-")
ot, nt2 = toks(baseline.get("tokens") or []), toks(cur.get("tokens") or [])
if ot != nt2:
    changed = True
    show("tokens ADDED", nt2-ot, "+"); show("tokens REMOVED", ot-nt2, "-")

if changed:
    print(">>> CHANGED vs baseline")
    sys.exit(1)
print("no changes vs baseline")
sys.exit(0)