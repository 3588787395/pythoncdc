#!/usr/bin/env python3
"""rr-v5 推导式形态语料工装（可重建，随仓库持久化）。

语料构造：15 条布尔链 CHAINS × 10 条表达式 EXPRS × 6 个宿主 HOSTS，
编号 k0001..k0900，k = (chain*10+expr)*6+host+1（每个用例在模块内是
一个函数，推导式自身是一个子 code object）。EXPRS[9] 是不含三元的
对照项（裸变量 `t`），用于核对过滤器整窗通道不误判。

口径：原源码 compile → pyc → pycdc.decompile_pyc(use_cfg=True) → 重新
compile，按 (opname, argval) 序列逐个 code object 比对（跳过
CACHE/EXTENDED_ARG/RESUME），并比对子 code object 名字集合。

用法：
  PYTHONPATH=/workspace python v5h.py <tag> [--dist]

输出：bad funcs = N / M；<tag>_bad.json（[{func, diffs}]）；
--dist 时按 chain/expr/host 统计并打印。
"""
import dis
import json
import os
import py_compile
import sys
import traceback

SKIP = {'CACHE', 'EXTENDED_ARG', 'RESUME'}

CHAINS = [
    'u and v or w',
    'u or v and w',
    '(u or v) and w',
    'u and (v or w)',
    'not (u and v) or w',
    'not (u or v) and w',
    'u and (v or w) and t',
    '(u or v) and (w or t)',
    'u or (v and w) or t',
    '(u and v) or (w and t) or u',
    'u and v and w or t',
    'u or v or w and t',
    'not u and not v or w',
    'u and not (v or w)',
    '(not u or v) and (w or not t)',
]


def _tern(c):
    return '("p" if %s else "q")' % c


def exprs(c):
    t = _tern(c)
    return [
        t,
        't and %s' % t,
        '%s and t' % t,
        '%s or t' % t,
        't or %s' % t,
        '(1 if %s else 0) if t else 2' % c,
        't if (1 if %s else 0) else 2' % c,
        'not %s' % t,
        '%s == t' % t,
        't',
    ]


HOSTS = [
    ('elt', '[%s for x in xs]'),
    ('dkey', '{%s: x for x in xs}'),
    ('dval', '{x: %s for x in xs}'),
    ('gen', '(%s for x in xs)'),
    ('multi', '[%s for x in xs for y in xs]'),
    ('filt', '[x for x in xs if (%s)]'),
]


def build_corpus():
    lines = []
    meta = {}
    k = 0
    for ci, c in enumerate(CHAINS):
        for ei, e in enumerate(exprs(c)):
            for hi, (hname, tmpl) in enumerate(HOSTS):
                k += 1
                name = 'k%04d' % k
                lines.append('def %s(xs, u, v, w, t): return %s'
                             % (name, tmpl % e))
                meta[name] = (ci, ei, hname)
    return '\n'.join(lines) + '\n', meta


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


def compare(c1, c2):
    a, b = {}, {}
    walk(c1, '<module>', a)
    walk(c2, '<module>', b)
    diffs = {}
    for name, ca in a.items():
        cb = b.get(name)
        if cb is None:
            diffs[name] = ['MISSING in product']
            continue
        na, nb = _norm(ca), _norm(cb)
        if len(na) != len(nb):
            diffs[name] = ['CODE-LEN %d vs %d' % (len(na), len(nb))]
            continue
        for i, (x, y) in enumerate(zip(na, nb)):
            if x != y:
                diffs[name] = ['@%d: %r vs %r' % (i, x, y)]
                break
        ca_children = sorted(n for n in a if n.startswith(name + '/')
                             and n.count('/') == name.count('/') + 1)
        cb_children = sorted(n for n in b if n.startswith(name + '/')
                             and n.count('/') == name.count('/') + 1)
        if [n.rsplit('/', 1)[1] for n in ca_children] != \
                [n.rsplit('/', 1)[1] for n in cb_children]:
            diffs.setdefault(name, []).append(
                'CHILDREN %r vs %r'
                % ([n.rsplit('/', 1)[1] for n in ca_children],
                   [n.rsplit('/', 1)[1] for n in cb_children]))
    for name in b:
        if name not in a:
            diffs[name] = ['EXTRA in product']
    return diffs


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'cur'
    dist = '--dist' in sys.argv
    src, meta = build_corpus()
    work = '/tmp/v5h_%s' % tag
    os.makedirs(work, exist_ok=True)
    src_path = os.path.join(work, 'corpus.py')
    pyc_path = os.path.join(work, 'corpus.pyc')
    with open(src_path, 'w') as f:
        f.write(src)
    py_compile.compile(src_path, cfile=pyc_path, doraise=True)

    from pycdc import decompile_pyc
    try:
        out = decompile_pyc(pyc_path, use_cfg=True)
    except Exception:
        traceback.print_exc()
        print('DECOMPILE-FAIL')
        return 1
    out_path = os.path.join(work, 'out.py')
    with open(out_path, 'w') as f:
        f.write(out)
    try:
        c2 = compile(out, out_path, 'exec')
    except SyntaxError as exc:
        print('RECOMPILE-FAIL %s' % exc)
        return 1
    c1 = compile(src, os.path.join(work, 'orig.py'), 'exec')

    diffs = compare(c1, c2)
    bad = [{'func': n, 'diffs': d} for n, d in sorted(diffs.items())]
    na, nb = {}, {}
    walk(c1, '<module>', na)
    walk(c2, '<module>', nb)
    total = len(na)
    with open(os.path.join(work, '%s_bad.json' % tag), 'w') as f:
        json.dump(bad, f, indent=1)
    print('out.py -> %s' % out_path)
    print('bad json -> %s' % os.path.join(work, '%s_bad.json' % tag))
    print('bad funcs = %d / %d' % (len(bad), total))

    if dist:
        from collections import Counter
        cc, ce, ch = Counter(), Counter(), Counter()
        bad_cases = set()
        for item in bad:
            parts = item['func'].split('/')
            if len(parts) < 2:
                continue
            name = parts[1]
            bad_cases.add(name)
            if name in meta:
                ci, ei, hname = meta[name]
                cc[ci] += 1
                ce[ei] += 1
                ch[hname] += 1
        print('bad cases = %d / %d' % (len(bad_cases), len(meta)))
        print('per chain = %s' % dict(sorted(cc.items())))
        print('per expr  = %s' % dict(sorted(ce.items())))
        print('per host  = %s' % dict(sorted(ch.items())))
        for name in sorted(bad_cases):
            if name in meta:
                ci, ei, hname = meta[name]
                print('  %s chain=%d expr=%d host=%s' % (name, ci, ei, hname))
    return 0


if __name__ == '__main__':
    sys.exit(main())
