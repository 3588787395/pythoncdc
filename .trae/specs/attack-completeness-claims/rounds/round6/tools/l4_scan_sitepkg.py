#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外候选扫描器（系统 site-packages 版）。

与 l4_scan_candidates.py 同源，仅把默认根目录换成系统 site-packages，
并额外支持「按包名白名单」扫描（避免 torch/numpy 这类超大包）。
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l4_scan_candidates import FEATURES, classify, import_pyc  # noqa: E402

SKIP_DIR_PARTS = {
    '__pycache__', 'tests', 'test', 'dist-info', 'libs', 'include', 'bin',
    'share', 'lib', 'Scripts', 'data', 'docs', 'doc',
}


def scan_sitepackages(root: str, pkgs: list[str], max_bytes: int):
    out: list[dict] = []
    scanned = 0
    for pkg in pkgs:
        base = os.path.join(root, pkg)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
            for fn in filenames:
                if not fn.endswith('.py'):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    size = os.path.getsize(p)
                except OSError:
                    continue
                if size > max_bytes:
                    continue
                scanned += 1
                info = classify(p)
                if not info or not info['features']:
                    continue
                pyc = import_pyc(p)
                if not pyc:
                    continue
                out.append({'path': p, 'pyc': pyc, **info})
    return out, scanned


def main() -> int:
    argv = sys.argv[1:]
    out = None
    if '--out' in argv:
        i = argv.index('--out')
        out = argv[i + 1]
        del argv[i:i + 2]
    root = r'D:\Python\Lib\site-packages'
    pkgs = argv or ['anyio', 'starlette', 'fastapi', 'pydantic', 'httpx', 'attrs',
                    'tenacity', 'rich', 'click', 'packaging', 'pydantic_core',
                    'websockets', 'uvicorn', 'sniffio', 'h11', 'httpcore']
    cands, scanned = scan_sitepackages(root, pkgs, 400_000)
    cands.sort(key=lambda r: (-len(r['features']), r['path']))
    payload = json.dumps({'candidates': cands, 'scanned': scanned},
                         ensure_ascii=False, indent=1)
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(payload + '\n')
        print('[scan-sitepkg] %d candidates / %d scanned -> %s' % (len(cands), scanned, out))
    else:
        print(payload)
    return 0


if __name__ == '__main__':
    sys.exit(main())
