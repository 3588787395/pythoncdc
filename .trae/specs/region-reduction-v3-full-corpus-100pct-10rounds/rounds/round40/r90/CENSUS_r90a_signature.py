# -*- coding: utf-8 -*-
"""CENSUS_R90A_signature — corpus-wide census of the jump signature (one target reached by BOTH
a forward and a BACKWARD conditional jump inside the same code object), plus the per-code-object
structural counts a duplicated-while-test criterion would key on.

Read-only over .pyc bytes (marshal + dis); no product is written, so nothing can move.
usage: python -X utf8 CENSUS_r90a_signature.py <budget_sec> <pathlist> [start]
"""
import marshal
import os
import sys
import time
import types

sys.path.insert(0, 'D:/Temp/r90/DELIVER')
from jigsig import block_graph, jump_target, COND                      # noqa: E402

ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'


def code_objects(root, prefix='<module>'):
    stack = [(root, prefix)]
    while stack:
        c, path = stack.pop()
        nm = path + '.' + c.co_name if path else c.co_name
        yield c, nm
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                stack.append((k, nm))


def census(co):
    blocks = block_graph(co)
    fwd, bwd = {}, {}
    for s, body in blocks.items():
        last = body[-1]
        t = jump_target(last)
        if t is None or last.opname not in COND:
            continue
        kind = ('F' if 'FORWARD' in last.opname else
                'B' if 'BACKWARD' in last.opname else ('B' if t < s else 'F'))
        (fwd if kind == 'F' else bwd).setdefault(t, []).append(s)
    both = sorted(set(fwd) & set(bwd))
    ncopy = sum(1 for t in both if len(bwd[t]) >= 2)
    return both, fwd, bwd, ncopy, len(co.co_code) // 2, len(blocks)


def main():
    budget = float(sys.argv[1])
    paths = [l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    t0 = time.time()
    total_units = sig_units = files_hit = 0
    rows = []
    cursor = start
    for cursor in range(start, len(paths)):
        if time.time() - t0 > budget:
            print('BUDGET NEXT=%d processed=%d' % (cursor, total_units))
            sys.exit(3)
        p = paths[cursor]
        if not os.path.isfile(p):
            rel = p.replace(ROOT + os.sep, '').replace(ROOT + '/', '')
            p = os.path.join(ROOT, rel.replace('/', os.sep))
            if not os.path.isfile(p):
                continue
        try:
            data = open(p, 'rb').read()
            code = marshal.loads(data[16:])
        except Exception as exc:
            print('UNMARSHAL_FAIL %s %s' % (p, exc))
            continue
        hit_in_file = 0
        for co, nm in code_objects(code):
            total_units += 1
            both, fwd, bwd, ncopy, ni, nb = census(co)
            if both:
                sig_units += 1
                hit_in_file += 1
                rows.append('%s :: %s  instrs=%d blocks=%d BOTH=%s fwd=%s bwd=%s'
                            % (os.path.relpath(p, ROOT).replace('\\', '/'), nm, ni, nb, both,
                               {t: fwd[t] for t in both}, {t: bwd[t] for t in both}))
        if hit_in_file:
            files_hit += 1
            print('FILE %s units=%d signature_units=%d'
                  % (os.path.relpath(p, ROOT).replace('\\', '/'), total_units, hit_in_file))
    print('DONE files=%d units_scanned=%d signature_units=%d files_with_signature=%d elapsed=%.0fs'
          % (len(paths), total_units, sig_units, files_hit, time.time() - t0))
    with open('D:/Temp/r90/DELIVER/logs/CENSUS_r90a_signature_rows.txt', 'a', encoding='utf-8') as fh:
        fh.write('\n'.join(rows) + '\n')


if __name__ == '__main__':
    main()
