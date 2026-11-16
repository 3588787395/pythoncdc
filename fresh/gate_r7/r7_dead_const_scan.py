# -*- coding: utf-8 -*-
"""How often does the original pyc carry constants that no instruction loads?

Those "dead" pool entries are exactly what the decompiler cannot reproduce from
the instruction stream, so they bound the blast radius of any
"adopt-the-pool-residue" renderer change.  Read-only over the evidence ledger.
"""
from __future__ import annotations

import collections
import dis
import json
import marshal
import os
import types

ROOT = r'F:\Downloads\pythoncdc-main'
EV = r'D:\temp\opencode\cl_layout\gap\g3fix\semantic_v3m_b275_g3fix_merged.json'
OUT = r'D:\temp\opencode\cl_layout\r7\dead_const_scan.json'
LOG = os.path.join(ROOT, 'fresh', 'gate_r7', 'dead_const_scan.log')


def walk(code, out):
    out.append(code)
    for v in code.co_consts:
        if isinstance(v, types.CodeType):
            walk(v, out)
    return out


def unused_consts(code):
    loaded = set()
    for ins in dis.get_instructions(code):
        if ins.opname in ('LOAD_CONST', 'RETURN_CONST'):
            loaded.add(ins.arg)
        elif ins.opname == 'LOAD_CONST':
            loaded.add(ins.arg)
    dead = []
    for i, v in enumerate(code.co_consts):
        if i in loaded:
            continue
        if isinstance(v, types.CodeType):
            continue  # a nested code object is 'loaded' by MAKE_FUNCTION's tuple
        dead.append((i, type(v).__name__, repr(v)[:40]))
    return dead


def main():
    ev = json.load(open(EV, encoding='utf-8'))['records']
    tr = {e['id'] for e in json.load(open(r'D:\temp\opencode\cl_layout\gap\g3gap\r7_transfer.json',
                                          encoding='utf-8'))['entries']}
    rows = []
    counts = collections.Counter()
    for rec in ev:
        eid = rec['entry_id']
        verdict = rec['c4'].get('verdict')
        pyc = os.path.join(ROOT, rec['c2']['pyc_path'])
        try:
            top = marshal.loads(open(pyc, 'rb').read()[16:])
        except BaseException as exc:
            counts['pyc_unreadable'] += 1
            continue
        n_codes = 0
        n_dead = 0
        dead_detail = []
        for code in walk(top, []):
            n_codes += 1
            dead = unused_consts(code)
            if dead:
                n_dead += len(dead)
                if len(dead_detail) < 4:
                    dead_detail.append({'qualname': code.co_qualname, 'dead': dead})
        rows.append({'id': eid, 'verdict': verdict, 'transferred': eid in tr,
                     'codes': n_codes, 'dead_consts': n_dead, 'detail': dead_detail})
        if n_dead:
            counts['with_dead_%s' % verdict] += 1
        else:
            counts['no_dead_%s' % verdict] += 1
    payload = {'counts': dict(counts), 'rows': rows,
               'equal_with_dead': sum(1 for r in rows if r['verdict'] == 'EQUAL' and r['dead_consts']),
               'equal_total': sum(1 for r in rows if r['verdict'] == 'EQUAL'),
               'transferred': sum(1 for r in rows if r['transferred']),
               'transferred_with_dead': sum(1 for r in rows if r['transferred'] and r['dead_consts'])}
    json.dump(payload, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    with open(LOG, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('counts: %s\n' % payload['counts'])
        fh.write('EQUAL entries: %d, of them with dead pool consts: %d\n'
                 % (payload['equal_total'], payload['equal_with_dead']))
        fh.write('transferred (29): %d, of them with dead pool consts: %d\n'
                 % (payload['transferred'], payload['transferred_with_dead']))
        for r in rows:
            if r['dead_consts'] and (r['verdict'] == 'EQUAL'):
                fh.write('  EQUAL %-18s codes=%d dead=%d %s\n'
                         % (r['id'], r['codes'], r['dead_consts'], r['detail']))
    print(json.dumps({k: payload[k] for k in ('counts', 'equal_total', 'equal_with_dead',
                                             'transferred', 'transferred_with_dead')},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
