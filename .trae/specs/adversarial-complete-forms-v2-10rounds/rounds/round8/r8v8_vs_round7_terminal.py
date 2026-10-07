#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r8v8 站桩读数 vs round7 终态（r7v7fix_* 证据 JSON）逐单元漂移检查。
零回退判据：每文件 units 与失败单元集合与 round7 终态逐位一致（WORSE=0 且 diff=0 即零漂移）。
输出 r8v8_vs_round7_terminal.json。只读，不改源码。"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R7 = os.path.abspath(os.path.join(HERE, '..', 'round7'))
PREFIX = 'F:/Downloads/pythoncdc-main/'


def norm(p):
    return p.replace('\\', '/').replace(PREFIX, '')


def load(path):
    d = json.load(open(path, encoding='utf-8'))
    rows = d['rows'] if isinstance(d, dict) and 'rows' in d else d
    out = {}
    for r in rows:
        out[norm(r['pyc'])] = (r.get('units_success'), r.get('units_total'),
                               tuple(sorted(f.strip() for f in (r.get('failures') or []))))
    return out


FACES = [
    ('round2face', 'r7v7fix_regress_round2face.json', 'r8v8_regress_round2face.json'),
    ('probe42', 'r7v7fix_regress_probe42.json', 'r8v8_regress_probe42.json'),
    ('round1face', 'r7v7fix_full_round1face.json', 'r8v8_full_round1face.json'),
    ('residual', 'r7v7fix_full_residual_a.json', 'r8v8_full_residual_a.json'),
    ('residual', 'r7v7fix_full_residual_b.json', 'r8v8_full_residual_b.json'),
    ('oldface', 'r7v7fix_full_oldface_a.json', 'r8v8_full_oldface_a.json'),
    ('oldface', 'r7v7fix_full_oldface_b.json', 'r8v8_full_oldface_b.json'),
    ('quotation', 'r7v7fix_quotation.json', 'r8v8_quotation.json'),
]

out = []
for name, base, new in FACES:
    b = load(os.path.join(R7, base))
    n = load(os.path.join(HERE, new))
    common = sorted(set(b) & set(n))
    miss_f = sorted(set(b) - set(n))
    extra_f = sorted(set(n) - set(b))
    diffs = []
    worse = 0
    for p in common:
        bu, bt, bf = b[p]
        nu, nt, nf = n[p]
        if bu != nu or bf != nf:
            diffs.append({'pyc': p, 'base': '%s/%s' % (bu, bt), 'new': '%s/%s' % (nu, nt),
                          'fail_removed': sorted(set(bf) - set(nf)),
                          'fail_added': sorted(set(nf) - set(bf))})
            if (nu or 0) < (bu or 0):
                worse += 1
    su_b = sum(v[0] or 0 for v in b.values())
    st_b = sum(v[1] or 0 for v in b.values())
    su_n = sum(v[0] or 0 for v in n.values())
    st_n = sum(v[1] or 0 for v in n.values())
    out.append({'face': name, 'base_json': base, 'new_json': new,
                'base_units': '%d/%d' % (su_b, st_b), 'new_units': '%d/%d' % (su_n, st_n),
                'common': len(common), 'missing_files': miss_f, 'extra_files': extra_f,
                'unit_diffs': diffs, 'WORSE': worse})

json.dump({'compare': 'r8v8 vs round7 terminal (r7v7fix_*)', 'faces': out},
          open(os.path.join(HERE, 'r8v8_vs_round7_terminal.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
tot_w = sum(f['WORSE'] for f in out)
tot_d = sum(len(f['unit_diffs']) for f in out)
for f in out:
    print(f['face'], f['base_json'], 'base', f['base_units'], 'new', f['new_units'],
          'WORSE', f['WORSE'], 'diffs', len(f['unit_diffs']),
          'miss', len(f['missing_files']), 'extra', len(f['extra_files']))
print('TOTAL WORSE vs round7 terminal =', tot_w, '; unit diffs =', tot_d)
