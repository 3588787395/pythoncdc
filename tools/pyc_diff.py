#!/usr/bin/env python3
"""pyc 反编译结果字节码对照工具（轮次迭代基础设施）。

把「原 pyc」与「反编译产出的 OK.py」编译回去的字节码逐条并排打印，
供测试工程师定位首个不一致点。

用法（必须用 Python 3.11.7，pyc 为 3.11 魔数 a70d0d0a）：
    D:/Python/python.exe tools/pyc_diff.py <pyc> <ok_py> <func_name>
    D:/Python/python.exe tools/pyc_diff.py <pyc> <ok_py> -a            # 全部函数
    D:/Python/python.exe tools/pyc_diff.py <pyc> <ok_py> <func> -c 40  # 上下文 40 条
"""
import argparse
import importlib.util
import marshal
import py_compile
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from testqouter.round1.base import get_bytecode_instructions  # noqa: E402


def _load_code(p):
    with open(p, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def _compile_ok(ok_py):
    cfile = py_compile.compile(ok_py, doraise=True, quiet=2)
    if cfile is None:
        cfile = importlib.util.cache_from_source(ok_py)
    return _load_code(cfile)


def _find(co, name):
    if (co.co_name or '<module>') == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = _find(c, name)
            if r:
                return r
    return None


def _names(co, acc):
    acc.append(co.co_name or '<module>')
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            _names(c, acc)
    return acc


def diff_func(orig_co, dec_co, name, ctx=None):
    o = _find(orig_co, name)
    d = _find(dec_co, name)
    if o is None:
        return [f'  [missing in orig] {name}']
    if d is None:
        return [f'  [missing in decomp] {name}']
    oi = get_bytecode_instructions(o)
    di = get_bytecode_instructions(d)
    out = [f'==== {name}  orig={len(oi)} decomp={len(di)}']
    first = None
    n = max(len(oi), len(di))
    for i in range(n):
        a = f'{oi[i].opname} {oi[i].argrepr}' if i < len(oi) else '-'
        b = f'{di[i].opname} {di[i].argrepr}' if i < len(di) else '-'
        same = a == b
        if not same and first is None:
            first = i
        if ctx is None or first is None or i >= first - ctx:
            out.append(f'{"   " if same else ">> "}{i:4d} | {a[:56]:56s} | {b[:56]}')
        if ctx is not None and first is not None and i > first + ctx:
            out.append(f'  ... ({n - i} more)')
            break
    out.append(f'---- first_diff_index={first}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pyc')
    ap.add_argument('ok_py')
    ap.add_argument('func', nargs='?', default=None)
    ap.add_argument('-a', '--all', action='store_true')
    ap.add_argument('-c', '--context', type=int, default=None)
    args = ap.parse_args()

    orig = _load_code(args.pyc)
    dec = _compile_ok(args.ok_py)

    if args.all:
        names = _names(orig, [])
        for nm in names:
            for line in diff_func(orig, dec, nm, args.context):
                print(line)
        return 0
    if not args.func:
        print(_names(orig, []))
        return 0
    for line in diff_func(orig, dec, args.func, args.context):
        print(line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
