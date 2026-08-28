#!/usr/bin/env python3
"""按过滤器后的指令流查看某函数原/反编译字节码差异（索引与 baseline 一致）。

用法： D:/Python/python.exe view.py <pyc> <func> [-c N] [-s START]
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'testqouter' / 'round1'))

import pyc_diff as pd  # noqa: E402
from base import _filter_noise_instrs, _normalize_argval  # noqa: E402


JUMPY = ('JUMP_', 'POP_JUMP_', 'FOR_ITER', 'SEND', 'SETUP_')


def fmt(i, nojump=False):
    av = _normalize_argval(i.argval)
    if nojump and i.opname.startswith(JUMPY):
        return i.opname
    s = f'{i.opname}'
    if i.argrepr:
        s += f' {av!r}'
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pyc')
    ap.add_argument('func')
    ap.add_argument('-c', '--context', type=int, default=12)
    ap.add_argument('-s', '--start', type=int, default=None)
    ap.add_argument('-j', '--nojump', action='store_true')
    args = ap.parse_args()

    orig = pd._load_code(args.pyc)
    okp = str(Path(args.pyc).with_suffix('')) + 'OK.py'
    dec = pd._compile_ok(okp)
    o = pd._find(orig, args.func)
    d = pd._find(dec, args.func)
    oi = _filter_noise_instrs(pd.get_bytecode_instructions(o))
    di = _filter_noise_instrs(pd.get_bytecode_instructions(d))
    print(f'==== {args.func}  orig={len(oi)} decomp={len(di)}')
    first = None
    n = max(len(oi), len(di))
    for i in range(n):
        a = fmt(oi[i], args.nojump) if i < len(oi) else '-'
        b = fmt(di[i], args.nojump) if i < len(di) else '-'
        same = a == b
        if not same and first is None:
            first = i
    lo = 0 if args.start is not None else max(0, (first or 0) - args.context)
    hi = n if args.start is not None else min(n, (first or 0) + args.context + 1)
    lo = args.start if args.start is not None else lo
    for i in range(lo, hi):
        a = fmt(oi[i], args.nojump) if i < len(oi) else '-'
        b = fmt(di[i], args.nojump) if i < len(di) else '-'
        same = a == b
        print(f'{"   " if same else ">> "}{i:4d} | {a[:58]:58s} | {b[:58]}')
    print(f'---- first_diff_index={first}  (baseline index)')


if __name__ == '__main__':
    main()
