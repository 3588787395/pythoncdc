#!/usr/bin/env python3
"""探针：对一个源文件做 compile -> decompile -> compile，打印源码/反编译结果/指令差异。

用法:
    D:/Python/python.exe probe.py <src_file>
    D:/Python/python.exe probe.py -   # 从 stdin 读
    D:/Python/python.exe probe.py --code 'def f(): ...'
"""
import dis
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / 'core' / 'cfg').is_dir() and (p / 'pycdc.py').is_file():
            return p
    raise RuntimeError(f'未找到项目根目录: {start}')


ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from core.cfg import decompile  # noqa: E402

NOISE_OPS = {'NOP', 'EXTENDED_ARG', 'PRECALL', 'COPY_FREE_VARS', 'MAKE_CELL'}


def walk(co):
    yield co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c)


def instrs(co):
    return [i for i in dis.get_instructions(co) if i.opname not in NOISE_OPS]


def _fmt(i):
    if isinstance(i.argval, types.CodeType):
        return f'{i.opname} <code object {i.argval.co_name}>'
    s = i.argrepr.strip()
    return f'{i.opname} {s}' if s else i.opname


def main():
    args = sys.argv[1:]
    if args and args[0] == '--code':
        src = args[1]
        name = '<code>'
    elif args and args[0] == '-':
        src = sys.stdin.read()
        name = '<stdin>'
    else:
        p = Path(args[0])
        src = p.read_text(encoding='utf-8')
        name = str(p)

    c_orig = compile(src, name, 'exec')
    out = decompile(src, name)
    print('===== SOURCE =====')
    print(src)
    print('===== DECOMPILED =====')
    print(out)
    print('===== ORIG dis =====')
    for co in walk(c_orig):
        print(f'--- code object {co.co_name} ---')
        for k, i in enumerate(instrs(co)):
            print(f'{k:4d} {i.offset:5d} {_fmt(i)}')
    try:
        c_dec = compile(out, name, 'exec')
    except SyntaxError as e:
        print(f'!! 反编译产物无法编译: {e}')
        return
    print('===== DECOMP dis =====')
    for co in walk(c_dec):
        print(f'--- code object {co.co_name} ---')
        for k, i in enumerate(instrs(co)):
            print(f'{k:4d} {i.offset:5d} {_fmt(i)}')
    print('===== DIFF =====')
    la, lb = list(walk(c_orig)), list(walk(c_dec))
    if len(la) != len(lb):
        print('code object 数量/顺序不同:')
        print('  orig  :', [c.co_name for c in la])
        print('  decomp:', [c.co_name for c in lb])
        return
    for x, y in zip(la, lb):
        if x.co_code == y.co_code and x.co_names == y.co_names:
            print(f'[OK ] {x.co_name}')
            continue
        print(f'[DIFF] {x.co_name}  names={x.co_names} vs {y.co_names}')
        ia, ib = instrs(x), instrs(y)
        n = max(len(ia), len(ib))
        shown = 0
        for k in range(n):
            ra = _fmt(ia[k]) if k < len(ia) else '<EOF>'
            rb = _fmt(ib[k]) if k < len(ib) else '<EOF>'
            if ra != rb:
                print(f'  #{k:4d}  orig={ra!r}   decomp={rb!r}')
                shown += 1
                if shown > 40:
                    print('  ...')
                    break


if __name__ == '__main__':
    main()
