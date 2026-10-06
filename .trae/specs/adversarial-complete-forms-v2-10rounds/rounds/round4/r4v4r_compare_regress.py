#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round4 复核（Task 4.3）：站桩回归对照。只读，不改源码。
输出 r4v4r_station_regress_compare.json（独立复跑读数 vs 承接基线）。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, '..')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')


def parse_tail(entry):
    fails, status, us, ut = [], None, None, None
    for line in entry.get('tail', []) or []:
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
        if FAIL_RE.match(line):
            fails.append(line.strip())
    return {'status': status, 'units_success': us, 'units_total': ut, 'failures': fails}


def load_list_tail(path):
    d = json.load(open(path, encoding='utf-8'))
    return {e['pyc']: parse_tail(e) for e in d}


def load_list_full(path):
    d = json.load(open(path, encoding='utf-8'))
    return {e['pyc']: {'status': e.get('status'), 'units_success': e.get('units_success'),
                       'units_total': e.get('units_total'), 'failures': e.get('failures', [])}
            for e in d}


def load_rows(path):
    d = json.load(open(path, encoding='utf-8'))
    rows = d['rows'] if isinstance(d, dict) else d
    out = {}
    for r in rows:
        out[r['pyc']] = {'status': r.get('status'), 'units_success': r.get('units_success'),
                         'units_total': r.get('units_total'), 'failures': r.get('failures', []) or []}
    return out


def load_oldface(path):
    d = json.load(open(path, encoding='utf-8'))
    return {k: {'status': v.get('status'), 'units_success': v.get('units_success'),
                'units_total': v.get('units_total'), 'failures': v.get('failures', []) or []}
            for k, v in d.items()}


def norm(p):
    return p.replace('\\', '/').replace('F:/Downloads/pythoncdc-main/', '')


def merge(*dicts):
    m = {}
    for d in dicts:
        m.update(d)
    return m


def compare(name, base, new, unit_level):
    bk = {norm(k): v for k, v in base.items()}
    nk = {norm(k): v for k, v in new.items()}
    common = sorted(set(bk) & set(nk))
    only_base = sorted(set(bk) - set(nk))
    only_new = sorted(set(nk) - set(bk))
    rows = []
    same = improved = worsened = 0
    for p in common:
        b, n = bk[p], nk[p]
        b_u, n_u = b['units_success'], n['units_success']
        if b_u is None or n_u is None:
            verdict = 'unknown'
        elif n_u < b_u:
            verdict = 'WORSE'
        elif n_u > b_u:
            verdict = 'improved'
        else:
            verdict = 'same'
        miss = sorted(set(b['failures']) - set(n['failures']))
        extra = sorted(set(n['failures']) - set(b['failures']))
        if verdict == 'WORSE':
            worsened += 1
        elif verdict == 'improved':
            improved += 1
        else:
            same += 1
        if verdict != 'same' or (unit_level and (miss or extra)) or only_base:
            rows.append({'pyc': p, 'verdict': verdict, 'base_units': b_u, 'new_units': n_u,
                         'base_status': b['status'], 'new_status': n['status'],
                         'fail_missing': miss, 'fail_extra': extra})
    b_tot = sum(v['units_success'] or 0 for v in bk.values())
    b_tot_u = sum(v['units_total'] or 0 for v in bk.values())
    n_tot = sum(v['units_success'] or 0 for v in nk.values())
    n_tot_u = sum(v['units_total'] or 0 for v in nk.values())
    return {'face': name, 'base_files': len(bk), 'new_files': len(nk),
            'common': len(common), 'only_base': only_base, 'only_new': only_new,
            'base_units': '%d/%d' % (b_tot, b_tot_u), 'new_units': '%d/%d' % (n_tot, n_tot_u),
            'same': same, 'improved': improved, 'worsened': worsened,
            'unit_level_compared': unit_level, 'details': rows}


def main():
    faces = []
    faces.append(compare('round2face',
                         load_list_tail(os.path.join(R, 'round2', 'r2_regress_replay.json')),
                         load_list_tail(os.path.join(HERE, 'r4v4r_regress_round2face.json')), False))
    faces.append(compare('probe42',
                         load_list_tail(os.path.join(R, 'round2', 'r2_probe_results.json')),
                         load_list_tail(os.path.join(HERE, 'r4v4r_regress_probe42.json')), False))
    faces.append(compare('round1face',
                         load_rows(os.path.join(R, 'round1', 'r1_sentry_replay.json')),
                         load_list_full(os.path.join(HERE, 'r4v4r_full_round1face.json')), True))
    faces.append(compare('residual',
                         load_rows(os.path.join(R, 'round1', 'r1_residual_replay.json')),
                         merge(load_list_full(os.path.join(HERE, 'r4v4r_full_residual_a.json')),
                               load_list_full(os.path.join(HERE, 'r4v4r_full_residual_b.json'))), True))
    faces.append(compare('oldface',
                         load_oldface(os.path.join(R, 'round3', 'r3v2_oldface_baseline.json')),
                         merge(load_list_full(os.path.join(HERE, 'r4v4r_full_oldface_a.json')),
                               load_list_full(os.path.join(HERE, 'r4v4r_full_oldface_b.json'))), True))
    out = {'faces': faces}
    with open(os.path.join(HERE, 'r4v4r_station_regress_compare.json'), 'w',
              encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for fc in faces:
        print('%-11s base=%s new=%s common=%d same=%d improved=%d WORSE=%d only_base=%d only_new=%d'
              % (fc['face'], fc['base_units'], fc['new_units'], fc['common'],
                 fc['same'], fc['improved'], fc['worsened'], len(fc['only_base']), len(fc['only_new'])))
        for d in fc['details']:
            if d['verdict'] != 'same' or d['fail_extra'] or d['fail_missing']:
                print('   %-9s %-55s %s->%s miss=%s extra=%s'
                      % (d['verdict'], d['pyc'], d['base_units'], d['new_units'],
                         len(d['fail_missing']), len(d['fail_extra'])))
        if fc['only_base']:
            print('   only_base:', fc['only_base'])


if __name__ == '__main__':
    main()