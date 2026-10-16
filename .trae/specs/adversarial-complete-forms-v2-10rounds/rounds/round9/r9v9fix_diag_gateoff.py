#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B124 诊断：gate-off 下 e05/c4_09/matcher 的产物形态与读数（只读实验，结束还原）。

臂 = off_b104r3（[B104-R3] released 门整体关闭）+ control 对照。
产出：r9v9fix_diag_gateoff.json + 产物文本（D:\\Temp\\opencode\\r92_products）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
ANA = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
OUT = os.path.join(HERE, 'r9v9fix_diag_gateoff.json')
TMPOUT = r'D:\Temp\opencode\r92_products'

GATE_OLD = ("            if block in released:\r\n",
            "            if False and (block in released):\r\n")

PROBES = [
    ('e05', 'test_repros/round3/e05_g3_compare_chain.pyc',
     ['f_compare_chain6', 'f_compare_binop_inside', 'f_compare_subscript_inside']),
    ('c4_09', 'test_repros/round4/c4_09_chained_compare.pyc', ['m']),
    ('matcher', 'site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc', []),
    ('nb_b99', r'D:\Temp\mon\nb\nb_b99.pyc', []),
]

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def run(cmd, timeout=250):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'


def probe(name, rel, dump_units):
    full = rel if os.path.isabs(rel) else os.path.join(ROOT, rel.replace('/', os.sep))
    ok = os.path.join(TMPOUT, name + '_gateoff.py')
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
               'single', full, '--source', ok])
    status, us, ut = None, None, None
    for line in out.splitlines():
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in out.splitlines() if FAIL_RE.match(l)]
    dump = {}
    if os.path.exists(ok):
        txt = open(ok, encoding='utf-8', errors='replace').read()
        for u in dump_units:
            m = re.search(r'^(def[^\n]*%s\(.*?\n(?:.*\n)*?)(?=^\S|\Z)' % re.escape(u),
                          txt, re.M)
            if u == 'm':
                # CCMP.m 方法体
                m = re.search(r'(^class CCMP:\n(?:.*\n)*?)(?=^\S|\Z)', txt, re.M)
            if m:
                dump[u] = m.group(0)[:2000]
    return {'status': status, 'units_success': us, 'units_total': ut,
            'failures': fails, 'dump': dump, 'product': ok}


def main():
    arm = sys.argv[1] if len(sys.argv) > 1 else 'off'
    os.makedirs(BAKDIR, exist_ok=True)
    base = {}
    for name in ('region_analyzer.py', 'region_ast_generator.py'):
        src = os.path.join(ROOT, 'core', 'cfg', name)
        dst = os.path.join(BAKDIR, name)
        with open(src, 'rb') as f:
            data = f.read()
        base[name] = hashlib.sha256(data).hexdigest()[:16]
        with open(dst, 'wb') as g:
            g.write(data)
    res = {'arm': arm, 'base_shas': base, 'probes': {}}
    try:
        if arm == 'off':
            text = open(ANA, 'rb').read().decode('utf-8')
            assert text.count(GATE_OLD[0]) == 1, 'gate anchor not unique'
            with open(ANA, 'wb') as f:
                f.write(text.replace(GATE_OLD[0], GATE_OLD[1]).encode('utf-8'))
        for name, rel, dumps in PROBES:
            if not os.path.exists(rel if os.path.isabs(rel) else
                                  os.path.join(ROOT, rel.replace('/', os.sep))):
                continue
            r = probe(name, rel, dumps)
            res['probes'][name] = r
            print('[%-8s %-8s] %-8s %s/%s fails=%d' % (
                arm, name, r['status'], r['units_success'], r['units_total'],
                len(r['failures'])), flush=True)
    finally:
        for name in ('region_analyzer.py', 'region_ast_generator.py'):
            with open(os.path.join(BAKDIR, name), 'rb') as f:
                data = f.read()
            with open(os.path.join(ROOT, 'core', 'cfg', name), 'wb') as f:
                f.write(data)
            cur = sha(os.path.join(ROOT, 'core', 'cfg', name))
            assert cur == base[name], 'RESTORE FAILED %s' % name
        print('-> restored OK')
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('-> ' + os.path.basename(OUT))


if __name__ == '__main__':
    main()
