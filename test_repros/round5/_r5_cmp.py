#!/usr/bin/env python3
"""round5 规范化指令对照:code object 身份(文件名/地址/行号)归一为名字后逐指令 diff。
用法: python test_repros/round5/_r5_cmp.py <orig.pyc> <OK.py> [qualname过滤]
只读判据配套,不修改 core/ 与 scripts/。
"""
import sys
import os
import marshal
import dis

NOISE = {'RESUME', 'CACHE', 'EXTENDED_ARG', 'PRECALL'}


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def walk(code, prefix=''):
    yield prefix or '<module>', code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            yield from walk(c, (prefix + '.' if prefix else '') + c.co_name)


def norm(val):
    if hasattr(val, 'co_code'):
        return '<code:%s>' % val.co_name
    if isinstance(val, tuple):
        return tuple(norm(v) for v in val)
    if isinstance(val, frozenset):
        return ('FROZENSET', tuple(sorted(map(str, val))))
    return val


def instrs(code):
    out = []
    for i in dis.get_instructions(code):
        if i.opname in NOISE:
            continue
        out.append((i.offset, i.opname, norm(i.argval)))
    return out


def main():
    pyc, src = sys.argv[1], sys.argv[2]
    flt = sys.argv[3] if len(sys.argv) > 3 else ''
    co = load_pyc(pyc)
    with open(src, encoding='utf-8-sig') as f:
        text = f.read()
    cj = compile(text, os.path.basename(pyc), 'exec', dont_inherit=True)
    left = dict(walk(co))
    right = dict(walk(cj))
    for name in left:
        if flt and flt not in name:
            continue
        ci = left[name]
        cj2 = right.get(name)
        if cj2 is None:
            print('[%s] MISSING in decompiled tree' % name)
            continue
        a, b = instrs(ci), instrs(cj2)
        n = max(len(a), len(b))
        diffs = []
        for idx in range(n):
            ea = a[idx] if idx < len(a) else None
            eb = b[idx] if idx < len(b) else None
            if ea != eb:
                diffs.append((idx, ea, eb))
        if not diffs:
            continue
        print('[%s] %d diffs (orig %d / decomp %d instrs)' % (name, len(diffs), len(a), len(b)))
        for idx, ea, eb in diffs[:8]:
            ctx_l = a[idx - 1][1] if idx > 0 and idx - 1 < len(a) else '-'
            print('  >> @%d: o=%s   d=%s   (o_prev=%s)' % (idx, ea, eb, ctx_l))


if __name__ == '__main__':
    main()
