#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外候选扫描器。

目的：在**语料外**的真实 Python 源码树（系统 stdlib / site-packages + 仓内自有模块）
中枚举含指定语言特征的候选文件，供 §2 语料外差分取样。

输出：JSON（stdout），字段：
  candidates: [ {path, pyc, features, bytes, loc} ... ]
  scanned:   扫描过的 .py 文件数
  skipped:   跳过原因计数

约束：
  * 只读；不写仓库树。
  * 特征判定基于**源码文本**（不是字节码），因为 §2 需要「读源码判断语义」。
  * `except*` 特征用 `except*` 关键字正则（3.11 语法）。
"""
from __future__ import annotations

import json
import os
import re
import sys

SKIP_DIR_PARTS = {
    'site-packages', 'test', 'tests', 'idlelib', 'lib2to3', 'encodings',
    'turtledemo', 'tkinter', 'distutils', '__pycache__',
}

FEATURES = {
    'except_star': re.compile(r'^\s*except\*', re.M),
    'pep604': re.compile(r':\s*[A-Za-z_][\w\.]*\s*\|\s*[A-Za-z_][\w\.]*'),
    'dataclass': re.compile(r'@dataclass\b'),
    'async_def': re.compile(r'\basync\s+def\b'),
    'generator': re.compile(r'\byield\b'),
    'fstring': re.compile(r'\bf["\']'),
    'annot': re.compile(r'->\s*[A-Za-z_]'),
    'decorator_chain': re.compile(r'^\s*@\w[\w\.]*\s*\n\s*@\w', re.M),
    'walrus': re.compile(r':='),
    'match_stmt': re.compile(r'^\s*match\s+.+:\s*$', re.M),
    'pos_only': re.compile(r'def\s+\w+\s*\([^)]*,/'),
}


def classify(path: str) -> dict:
    try:
        text = open(path, encoding='utf-8', errors='replace').read()
    except OSError:
        return {}
    feats = [name for name, rx in FEATURES.items() if rx.search(text)]
    return {'features': feats, 'bytes': os.path.getsize(path), 'loc': text.count('\n') + 1}


def scan(roots: list[str], max_bytes: int) -> tuple[list[dict], int, dict]:
    out: list[dict] = []
    scanned = 0
    skipped: dict[str, int] = {}
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
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
                    skipped['too_big'] = skipped.get('too_big', 0) + 1
                    continue
                scanned += 1
                info = classify(p)
                if not info:
                    continue
                pyc = import_pyc(p)
                if not pyc:
                    skipped['no_pyc'] = skipped.get('no_pyc', 0) + 1
                    continue
                out.append({'path': p, 'pyc': pyc, **info})
    return out, scanned, skipped


def import_pyc(src: str) -> str | None:
    """按 CPython 的 __pycache__ 命名规则定位同目录的 .pyc。"""
    d, base = os.path.split(src)
    cache = os.path.join(d, '__pycache__')
    stem = os.path.splitext(base)[0]
    if not os.path.isdir(cache):
        return None
    for fn in os.listdir(cache):
        if fn.startswith(stem + '.') and fn.endswith('.pyc'):
            return os.path.join(cache, fn)
    return None


def main() -> int:
    argv = sys.argv[1:]
    out = None
    if '--out' in argv:
        i = argv.index('--out')
        out = argv[i + 1]
        del argv[i:i + 2]
    roots = argv or [r'D:\Python\Lib']
    max_bytes = 400_000
    cands, scanned, skipped = scan(roots, max_bytes)
    cands.sort(key=lambda r: (-len(r['features']), r['path']))
    payload = json.dumps({'candidates': cands, 'scanned': scanned, 'skipped': skipped},
                         ensure_ascii=False, indent=1)
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(payload + '\n')
        print('[scan] %d candidates / %d scanned -> %s' % (len(cands), scanned, out))
    else:
        print(payload)
    return 0


if __name__ == '__main__':
    sys.exit(main())
