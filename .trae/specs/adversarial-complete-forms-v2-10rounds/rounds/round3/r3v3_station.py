#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round3 Task 3.3 独立复跑：站桩 6 面（先 regen 再 batch verify），只读 core/，
只写 r3v3_* 证据。所有路径以本目录为锚，绝不覆盖 r3v2_* 评审/FIX 证据。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUNDS = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUNDS, '..', '..', '..', '..'))
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

FACES = {
    'round2face': (os.path.join(ROUNDS, 'round2', 'r2_regress_replay.json'), 'list'),
    'probe42': (os.path.join(ROUNDS, 'round2', 'r2_probe_results.json'), 'list'),
    'round1face': (os.path.join(ROUNDS, 'round1', 'r1_sentry_replay.json'), 'rows'),
    'residual': (os.path.join(ROUNDS, 'round1', 'r1_residual_replay.json'), 'rows'),
    'oldface': (os.path.join(HERE, 'r3v2_oldface_baseline.json'), 'keys'),
}
QUOTATION = os.path.join(ROOT, 'site-packages', 'fly', 'data', 'quotation.pyc')


def norm(p):
    p = p.replace('\\', '/')
    pre = 'F:/Downloads/pythoncdc-main/'
    if p.startswith(pre):
        p = p[len(pre):]
    if p.startswith('/'):
        p = p[len(ROOT.replace('\\', '/')) + 1:]
    return p


def face_pycs():
    out = {}
    for face, (path, kind) in FACES.items():
        d = json.load(open(path, encoding='utf-8-sig'))
        if kind == 'list':
            out[face] = [norm(e['pyc']) for e in d]
        elif kind == 'rows':
            out[face] = [norm(r['pyc']) for r in d['rows']]
        else:
            out[face] = [norm(k) for k in d.keys()]
    out['quotation'] = [norm(QUOTATION)]
    return out


def run(cmd, timeout=280):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    fp = face_pycs()
    uniq = []
    seen = set()
    for face, plist in fp.items():
        for p in plist:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
    # regen all OK.py
    for p in uniq:
        full = os.path.join(ROOT, p.replace('/', os.sep))
        ok = full[:-4] + 'OK.py'
        run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    index = os.path.join(HERE, 'r3v3_station_index.json')
    with open(index, 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{'path': p} for p in uniq], f, ensure_ascii=False, indent=1)
    rep = os.path.join(HERE, 'r3v3_station_results.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', index, '--json', rep], timeout=290)
    print('batch rc=%d' % rc)
    print('\n'.join(out.strip().splitlines()[-8:]))

    rows = {norm(r['pyc']): r for r in json.load(open(rep, encoding='utf-8'))['rows']}
    cmp_out = compare(fp, rows)
    cp = os.path.join(HERE, 'r3v3_station_compare.json')
    with open(cp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(cmp_out, f, ensure_ascii=False, indent=1)
    print('-> %s' % cp)


def _base_tail(path):
    d = json.load(open(path, encoding='utf-8-sig'))
    out = {}
    for e in d:
        status, us, ut = None, None, None
        fails = []
        for line in e.get('tail', []) or []:
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                fails.append(line.strip())
        out[norm(e['pyc'])] = {'status': status, 'units_success': us,
                               'units_total': ut, 'failures': fails}
    return out


def _base_rows(path):
    d = json.load(open(path, encoding='utf-8-sig'))
    rows = d['rows'] if isinstance(d, dict) else d
    return {norm(r['pyc']): {'status': r.get('status'),
                             'units_success': r.get('units_success'),
                             'units_total': r.get('units_total'),
                             'failures': r.get('failures') or []} for r in rows}


def _base_keys(path):
    d = json.load(open(path, encoding='utf-8-sig'))
    return {norm(k): {'status': v.get('status'), 'units_success': v.get('units_success'),
                      'units_total': v.get('units_total'),
                      'failures': v.get('failures') or []} for k, v in d.items()}


def fu(f):
    return f.split(': Failure')[0].strip()


def compare(fp, rows):
    out = {}
    for face, (path, kind) in FACES.items():
        if kind == 'list':
            base = _base_tail(path)
        elif kind == 'rows':
            base = _base_rows(path)
        else:
            base = _base_keys(path)
        res = _cmp_face(face, base, rows)
        out[face] = res
    # quotation single
    q = norm(QUOTATION)
    base_q = {'units_success': 152, 'units_total': 153,
              'failures': ['change_his_to_forward']}
    r = rows.get(q)
    out['quotation'] = {'face': 'quotation', 'base_units': '152/153',
                        'new_units': '%s/%s' % (r['units_success'], r['units_total']),
                        'new_status': r['status'],
                        'new_failure_count': len(r['failures'])}
    return out


def _cmp_face(face, base, rows):
    common = sorted(set(base) & set(rows))
    same = improved = worse = 0
    details = []
    for p in common:
        b, n = base[p], rows[p]
        bu, nu = b['units_success'], n['units_success']
        if bu is None or nu is None:
            v = 'unknown'
        elif nu < bu:
            v = 'WORSE'
        elif nu > bu:
            v = 'improved'
        else:
            v = 'same'
        if v == 'WORSE':
            worse += 1
        elif v == 'improved':
            improved += 1
        else:
            same += 1
        bf = set(fu(x) for x in b['failures'])
        nf = set(fu(x) for x in n['failures'])
        extra = sorted(nf - bf)
        miss = sorted(bf - nf)
        if v != 'same' or extra or miss:
            details.append({'pyc': p, 'verdict': v, 'base_units': bu, 'new_units': nu,
                            'base_status': b['status'], 'new_status': n['status'],
                            'new_extras': extra, 'fixed': miss})
    btot = sum(v['units_success'] or 0 for v in base.values())
    btot_u = sum(v['units_total'] or 0 for v in base.values())
    ntot = sum(rows[p]['units_success'] for p in common)
    ntot_u = sum(rows[p]['units_total'] for p in common)
    return {'face': face, 'base_files': len(base), 'new_files': len(rows),
            'common': len(common), 'only_base': sorted(set(base) - set(rows)),
            'base_units': '%d/%d' % (btot, btot_u),
            'new_units': '%d/%d' % (ntot, ntot_u),
            'same': same, 'improved': improved, 'worsened': worse,
            'details': details}


if __name__ == '__main__':
    main()
