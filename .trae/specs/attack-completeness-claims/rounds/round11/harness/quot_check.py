#!/usr/bin/env python3
"""真实语料回归工装：site-packages/fly/data/quotation.pyc 逐 code object 比对。

口径：pyc → pycdc.decompile_pyc(use_cfg=True) → 重新 compile →
按 (opname, argval) 序列逐 code object 比对（跳过 CACHE/EXTENDED_ARG/RESUME）。

用法：PYTHONPATH=/workspace python quot_check.py [tag]
输出：bad funcs = N / M；/tmp/quot_<tag>/<tag>_quot_bad.json
"""
import dis
import json
import marshal
import os
import sys

SKIP = {'CACHE', 'EXTENDED_ARG', 'RESUME'}


def _norm_argval(av):
    if hasattr(av, 'co_code'):
        return '<code %s>' % av.co_name
    if isinstance(av, (str, int, float, bool, type(None), tuple, frozenset)):
        return av
    return repr(av)


def _norm(co):
    return [(i.opname, _norm_argval(i.argval))
            for i in dis.get_instructions(co) if i.opname not in SKIP]


def walk(co, prefix, out):
    out[prefix] = co
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            walk(c, prefix + '/' + c.co_name, out)


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'cur'
    pyc = '/workspace/site-packages/fly/data/quotation.pyc'
    if not os.path.exists(pyc):
        print('pyc missing: %s' % pyc)
        return 1
    from pycdc import decompile_pyc
    out = decompile_pyc(pyc, use_cfg=True)
    work = '/tmp/quot_%s' % tag
    os.makedirs(work, exist_ok=True)
    out_path = os.path.join(work, 'out.py')
    with open(out_path, 'w') as f:
        f.write(out)
    try:
        c2 = compile(out, out_path, 'exec')
    except SyntaxError as exc:
        print('RECOMPILE-FAIL %s' % exc)
        return 1
    with open(pyc, 'rb') as f:
        f.read(16)
        co = marshal.load(f)
    a, b = {}, {}
    walk(co, '<module>', a)
    walk(c2, '<module>', b)
    bad = []
    for name, ca in a.items():
        cb = b.get(name)
        if cb is None:
            bad.append({'func': name, 'diffs': ['MISSING in product']})
            continue
        na, nb = _norm(ca), _norm(cb)
        if len(na) != len(nb):
            bad.append({'func': name,
                        'diffs': ['CODE-LEN %d vs %d' % (len(na), len(nb))]})
            continue
        for i, (x, y) in enumerate(zip(na, nb)):
            if x != y:
                bad.append({'func': name,
                            'diffs': ['@%d: %r vs %r' % (i, x, y)]})
                break
    for name in b:
        if name not in a:
            bad.append({'func': name, 'diffs': ['EXTRA in product']})
    with open(os.path.join(work, '%s_quot_bad.json' % tag), 'w') as f:
        json.dump(bad, f, indent=1)
    print('out.py -> %s' % out_path)
    print('bad funcs = %d / %d' % (len(bad), len(a)))
    for item in bad[:40]:
        print('  %s %s' % (item['func'], item['diffs']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
