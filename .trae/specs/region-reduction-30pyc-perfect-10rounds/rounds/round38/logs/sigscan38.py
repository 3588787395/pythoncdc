# -*- coding: utf-8 -*-
"""Round 38 exposure ruler: classify every mismatching function's aligned-diff signature.

For each mismatching function of the 27 partial files, align the two filtered instruction
token sequences (same normalisation as the strict gate) and print a compact signature of the
non-equal difflib opcodes. Goal: find how many functions share one shape before proposing a
same-level predicate.

usage: python -X utf8 sigscan38.py --in=p27_landed.jsonl --out=functsig38.txt
"""
import difflib
import importlib.util
import io
import json
import os
import sys
from collections import defaultdict

REPO = r'F:\Downloads\pythoncdc-main'
kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'D:/Temp/r38gate/r38'
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (str(r10._norm_arg(i)), i.opname)


rows = [json.loads(l) for l in io.open(os.path.join(ROOT, kw['in']), encoding='utf-8') if l.strip()]
assert len(rows) == 27, len(rows)
out = io.open(os.path.join(ROOT, kw['out']), 'w', encoding='utf-8', newline='\n')
groups = defaultdict(list)
unresolved = []
for r in rows:
    pyc = r['path']
    rel = pyc.replace('\\', '/').split('site-packages/')[-1]
    dst = os.path.join(ROOT, 'build_landed',
                       rel[:-4].replace('/', '__').replace(':', '_') + 'OK.py')
    origs = r10._load_map(pyc)
    decs = r10._compile_map(dst)
    for name, o_n, d_n, j, t in r['mism']:
        cands = [k for k in origs if k.split('.')[-1] == name or k.endswith('.' + name)]
        if len(cands) > 1:
            # Same co_name at several nesting levels (e.g. <module>.run_daily and
            # <module>.Scheduler.run_daily): keep only those the strict gate itself flags.
            cands = [k for k in cands if r10.strict_compare(origs[k], decs[k])[2]]
        if len(cands) != 1:
            unresolved.append('%s :: %s (%d/%d) keys=%s' % (rel, name, o_n, d_n, cands))
            continue
        key = cands[0]
        so = [tok(i) for i in r10.filtered(origs[key])]
        sd = [tok(i) for i in r10.filtered(decs[key])]
        ops = [(tag, i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in
               difflib.SequenceMatcher(a=so, b=sd, autojunk=False).get_opcodes()
               if tag != 'equal']
        # opnames that vanish from the original side / appear only in the product
        delops = sorted({so[k][1] for tag, i1, i2, j1, j2 in
                         difflib.SequenceMatcher(a=so, b=sd, autojunk=False).get_opcodes()
                         if tag in ('delete', 'replace') for k in range(i1, i2)})
        insops = sorted({sd[k][1] for tag, i1, i2, j1, j2 in
                         difflib.SequenceMatcher(a=so, b=sd, autojunk=False).get_opcodes()
                         if tag in ('insert', 'replace') for k in range(j1, j2)})
        sig = (tuple(ops), tuple(delops), tuple(insops))
        groups[sig].append('%s :: %s (%d/%d j%s t%s)' % (rel, name, o_n, d_n, j, t))
        out.write('%-72s %-34s %s | -%s +%s\n' % (
            rel, name, ' '.join('%s:%d/%d' % (a, b, c) for a, b, c in ops),
            ','.join(delops), ','.join(insops)))
out.close()

print('=== %d signature groups over %d functions ===' % (
    len(groups), sum(len(v) for v in groups.values())))
print('unresolved (name collisions the strict gate could not break): %d' % len(unresolved))
for u in unresolved:
    print('   ? ' + u)
for sig, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print('\n[%d] hunks=%s  deleted=%s  inserted=%s' % (
        len(members), sig[0], list(sig[1]), list(sig[2])))
    for m in members[:12]:
        print('      ' + m)
    if len(members) > 12:
        print('      ... %d more' % (len(members) - 12))
