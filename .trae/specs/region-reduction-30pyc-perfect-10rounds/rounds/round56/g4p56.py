# -*- coding: utf-8 -*-
"""G4' for Round 55 candidate 1: per-code-object strict A/B over every MOVED path.

A side = the repo products (current landed core). B side = the gated arm products.
Prints FIXED / BROKEN / CHANGED per code object so an officially-invisible
regression cannot hide behind MOVED + gained=[]/lost=[].
usage: python -X utf8 g4p55.py
"""
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BUILD = sys.argv[1] if len(sys.argv) > 1 else r'D:/Temp/r54gate/build_r55br'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r55sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

MOVED = [
    'IQCommon/common/main.pyc',
    'IQCommon/util/fileio_utils.pyc',
    'IQData/plugins/plugin_system_realquote/real_quote.pyc',
    'IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc',
    'fly/common/common.pyc',
    'fly/common/flytools.pyc',
    'fly/data/quote.pyc',
    'fly/dumpload/load_daily.pyc',
    'test_repros/round31_arm_terminal_join/r31a_witness.pyc',
]


def armpath(rel):
    if rel.startswith('test_repros/'):
        stem = (REPO + '/' + rel)[:-4].replace('/', '__').replace(':', '_') + 'OK.py'
    else:
        stem = rel[:-4].replace('/', '__') + 'OK.py'
    return os.path.join(BUILD, stem)


tf = tb = tc = 0
for rel in MOVED:
    under_sp = not rel.startswith('test_repros/')
    base = (REPO + '/site-packages/' if under_sp else REPO + '/') + rel
    pyc = os.path.abspath(base.replace('/', os.sep))
    prod_a = pyc[:-4] + 'OK.py'
    prod_b = armpath(rel)
    if not (os.path.exists(pyc) and os.path.exists(prod_a) and os.path.exists(prod_b)):
        print('%-56s SKIP a=%s b=%s' % (rel[-56:], os.path.exists(prod_a), os.path.exists(prod_b)))
        continue
    o = r10._load_map(pyc)
    A = r10._compile_map(prod_a)
    B = r10._compile_map(prod_b)
    fx = br = ch = 0
    for n in sorted(set(o) & set(A) & set(B)):
        ka, ma, ba = r10.strict_compare(o[n], A[n])
        kb, mb, bb = r10.strict_compare(o[n], B[n])
        ba, bb = bool(ba), bool(bb)
        if ba == bb:
            if str(ma) != str(mb):
                ch += 1
                print('   CHANGED %-40s %s %s -> %s %s' % (n.replace('<module>.', '')[:40],
                                                           ka, str(ma)[:34], kb, str(mb)[:34]))
        elif bb:
            br += 1
            print('   BROKEN  %-40s ok -> %s %s' % (n.replace('<module>.', '')[:40], kb, str(mb)[:44]))
        else:
            fx += 1
            print('   FIXED   %-40s %s %s -> ok' % (n.replace('<module>.', '')[:40],
                                                    ka, str(ma)[:40]))
    tf += fx
    tb += br
    tc += ch
    print('%-58s FIXED=%d BROKEN=%d CHANGED=%d' % (rel[-58:], fx, br, ch))
print('TOTAL FIXED=%d BROKEN=%d CHANGED=%d' % (tf, tb, tc))
