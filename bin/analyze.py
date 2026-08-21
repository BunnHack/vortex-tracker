#!/usr/bin/env python3
"""
Vortex Client Tracker — binary/string leak extractor.

Replicates the rizin/XRef + string-scan pass a human would do by hand on a
Vortex .exe and emits a JSON snapshot. Diffing snapshots across runs shows
what a new build leaked, changed, or removed — no manual rizin needed.

Usage:
    python3 analyze.py < Vortex.exe > latest.json
"""
import re, sys, hashlib, json

def printable(seg):
    return seg.decode('utf-8','replace').translate({c:'.' for c in range(256) if not (0x20<=c<0x7f)})

def eps_from(data):
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{5,}', data):
        t = m.group(0).decode('utf-8','replace')
        if re.match(r'^/(?:api|releases(?:-studio)?|download|studio)[A-Za-z0-9_\-/?&=:.]{0,60}', t):
            o = t.split('\x00')[0].split(' ')[0]
            if len(o) > 3:
                out.append(o)
    return sorted(set(out))

def env_toggles_from(data):
    toks = [x.decode() for x in re.findall(rb'[A-Z][A-Z_]{3,}[A-Z0-9]', data)]
    keep = []
    for t in toks:
        if any(x in t for x in ('_KHR','_EXT','_NV','_VK','_FEATURES_','_CREATE_INFO','_INFO_','_CMPX','_VNDF')):
            continue
        if len(t) > 48:
            continue
        if t.startswith(('VORTEX','WGPU','RUST_','BEVY_','CARGO_','WINIT_','LOCALAPPDATA')):
            keep.append(t)
        elif any(x in t for x in ('BACKEND','INSTANCE','_STAGE','_TOKEN','NO_UPDATE','_ADAPTER','NO_UPDATE')):
            keep.append(t)
    return sorted(set(keep))

def build_paths(data):
    s = set(
        m.group(0).decode('utf-8','replace')
        for m in re.finditer(rb'(?:/private/tmp|/Users/[A-Za-z0-9_]+|/build/|\.cargo/)[A-Za-z0-9_./:@\d\-]{4,}', data)
    )
    return sorted(s)[:400]

def tokens(data):
    # hardcoded credential-ish literals near header words
    toks = []
    for kw in [b'X-App-Token', b'pp_token', b'X-Hardware-Id', b'app_token', b'token', b'api_key']:
        for m in re.finditer(re.escape(kw), data):
            s=m.start()
            ctx = data[max(0,s-40):s+64]
            toks.append({"kw":kw.decode(), "off":hex(s), "ctx":printable(ctx)})
    return toks[:60]

def struct_defs(data):
    return sorted(set(
        m.group(0).decode('utf-8','replace')
        for m in re.finditer(rb'struct [A-Za-z0-9_]+ with \d+ elements', data)
    ))

def tokens_from(data):
    toks = []
    for kw in [b'X-App-Token', b'pp_token', b'X-Hardware-Id', b'app_token']:
        for m in re.finditer(re.escape(kw), data):
            s=m.start()
            toks.append({"kw":kw.decode(), "off":hex(s), "ctx":printable(data[max(0,s-30):s+48])})
    return toks[:60]

def version_hints(data):
    return sorted(set(
        m.group(0).decode('utf-8','replace')
        for m in re.finditer(rb'[0-9]+\.[0-9]+\.[0-9]+(?:windows)?', data)
    ))[:60]

def main():
    data = sys.stdin.buffer.read()
    rep = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "magic": data[:4].hex(),
        "version_hints": version_hints(data),
        "endpoints": eps_from(data),
        "env_toggles": env_toggles_from(data),
        "build_paths": build_paths(data),
        "tokens": tokens_from(data),
        "struct_defs": struct_defs(data),
    }
    print(json.dumps(rep, indent=2))
    return rep

if __name__ == "__main__":
    main()