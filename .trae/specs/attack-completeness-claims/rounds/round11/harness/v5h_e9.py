#!/usr/bin/env python3
"""为语料 EXPRS[9] 选一个「filt 宿主零失败」的形态（保持 900 例规模）。

对每个候选表达式 × 15 条链生成 filt 宿主用例（`[x for x in xs if (<E>)]`），
走 pycdc → 重编译 → 逐 code object 比对，打印失败数。
用法：PYTHONPATH=/workspace python v5h_e9.py
"""
import dis
import json
import os
import py_compile
import sys

SKIP = {'CACHE', 'EXTENDED_ARG', 'RESUME'}

CHAINS = [
    'u and v or w', 'u or v and w', '(u or v) and w', 'u and (v or w)',
    'not (u and v) or w', 'not (u or v) and w', 'u and (v or w) and t',
    '(u or v) and (w or t)', 'u or (v and w) or t', '(u and v) or (w and t) or u',
    'u and v and w or t', 'u or v or w and t', 'not u and not v or w',
    'u and not (v or w)', '(not u or v) and (w or not t)',
]

CANDS = {
    'not_eq': lambda c: '("p" if %s else "q") != t' % c,
    'in': lambda c: '("p" if %s else "q") in xs' % c,
    'is_': lambda c: '("p" if %s else "q") is t' % c,
    'len': lambda c: 'len(("p" if %s else "q"))' % c,
    'bool': lambda c: 'bool("p" if %s else "q")' % c,
    'neg': lambda c: '-(1 if %s else 0)' % c,
    'tuple': lambda c: '(("p" if %s else "q"), t)' % c,
    't_and0': lambda c: 't and (1 if %s else 0)' % c,
    'mul': lambda c: '("p" if %s else "q") * 2' % c,
    'str': lambda c: 'str("p" if %s else "q")' % c,
}


def norm(co):
    return [(i.opname, i.argval if not hasattr(i.argval, 'co_code') else '<code>')
            for i in dis.get_instructions(co) if i.opname not in SKIP]


def walk(co, prefix, out):
    out[prefix] = co
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            walk(c, prefix + '/' + c.co_name, out)


def count_bad(src, work):
    os.makedirs(work, exist_ok=True)
    p = os.path.join(work, 'c.py')
    pc = os.path.join(work, 'c.pyc')
    open(p, 'w').write(src)
    py_compile.compile(p, cfile=pc, doraise=True)
    from pycdc import decompile_pyc
    try:
        out = decompile_pyc(pc, use_cfg=True)
        c2 = compile(out, '<out>', 'exec')
    except Exception as exc:
        return 'FAIL(%s)' % type(exc).__name__
    c1 = compile(src, '<orig>', 'exec')
    a, b = {}, {}
    walk(c1, '<module>', a)
    walk(c2, '<module>', b)
    bad = 0
    for n, ca in a.items():
        cb = b.get(n)
        if cb is None or norm(ca) != norm(cb):
            bad += 1
    return bad


def main():
    for name, fn in CANDS.items():
        lines = []
        for ci, c in enumerate(CHAINS):
            lines.append('def c%02d(xs, u, v, w, t): return [x for x in xs if (%s)]'
                         % (ci, fn(c)))
        r = count_bad('\n'.join(lines) + '\n', '/tmp/v5h_e9/%s' % name)
        print('%-8s filt bad = %s / 15' % (name, r))
    return 0


if __name__ == '__main__':
    sys.exit(main())
