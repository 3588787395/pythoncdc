#!/usr/bin/env python3
"""有界的往返回归套件（Round 02 / 修复工程师）。

对一批纯 Python 源文件做 compile -> decompile -> compile，递归比对 co_code。
只统计 PASS/FAIL（不判定"为什么"），用于对比「修改前 / 修改后」的差分。

用法:
    D:/Python/python.exe roundtrip_suite.py <out.json> [max_files]
"""
import json
import sys
import types
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

HERE = Path(__file__).resolve().parent


def _find_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / 'core' / 'cfg').is_dir() and (p / 'pycdc.py').is_file():
            return p
    raise RuntimeError(start)


ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from core.cfg import decompile  # noqa: E402


def walk(co):
    yield co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c)


def roundtrip_ok(path: Path) -> bool:
    try:
        src = path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return False
    try:
        c_orig = compile(src, str(path), 'exec')
    except (SyntaxError, ValueError):
        return False
    try:
        out = decompile(src, str(path))
    except Exception:
        return False
    try:
        c_dec = compile(out, str(path), 'exec')
    except (SyntaxError, ValueError):
        return False
    la, lb = list(walk(c_orig)), list(walk(c_dec))
    if len(la) != len(lb):
        return False
    for x, y in zip(la, lb):
        if x.co_code != y.co_code:
            return False
        if x.co_names != y.co_names:
            return False
    return True


def collect(root: Path, limit: int, must_contain: str = ''):
    """挑选体量适中（3KB~80KB）的纯 Python 源文件，确定性排序。"""
    cands = []
    for p in sorted(root.rglob('*.py')):
        if 'test' in p.name.lower() or 'lib2to3' in str(p) or 'idlelib' in str(p):
            continue
        try:
            sz = p.stat().st_size
        except OSError:
            continue
        if not (3000 <= sz <= 80000):
            continue
        if must_contain:
            try:
                if must_contain not in p.read_text(encoding='utf-8', errors='replace'):
                    continue
            except OSError:
                continue
        cands.append(p)
        if len(cands) >= limit:
            break
    return cands


def main():
    out_path = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    import sysconfig
    stdlib = Path(sysconfig.get_paths()['stdlib'])
    must = sys.argv[3] if len(sys.argv) > 3 else ''
    files = collect(stdlib, limit, must)
    results = {}
    npass = 0
    for p in files:
        rel = str(p.relative_to(stdlib))
        ok = roundtrip_ok(p)
        results[rel] = ok
        npass += ok
        print(f'[{"PASS" if ok else "FAIL"}] {rel}')
    print(f'--- 总计 {len(files)}  PASS {npass}  FAIL {len(files) - npass}')
    out_path.write_text(json.dumps(results, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
