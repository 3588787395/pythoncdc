# -*- coding: utf-8 -*-
"""Sub-cluster the large instruction losses by NAME USAGE.

The original .py is not on disk (only .pyc), so "which statement vanished" is read
from the operand arguments instead: every instruction that references a name or a
constant is counted, and the product's recompiled code object is counted the same
way. A name/constant used N times in the original and M<N times in the product
points straight at the dropped statement, without touching source text.

usage: python -X utf8 loss54.py            (products on disk, no core execution)
"""
import collections
import dis
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r54sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

TARGETS = [
    ('IQEngine/plugins/plugin_system_log/__init__.pyc', '<module>.DefaultLogger.setup'),
    ('fly/data/quote_handler.pyc', '<module>.get_kline_local'),
    ('IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc',
     '<module>.PluginRiskCalculation.get_TradeMode_trades'),
    ('fly/data/quote.pyc', '<module>.check_limit'),
]


def usage(co):
    c = collections.Counter()
    for ins in dis.get_instructions(co):
        if ins.opname in ('NOP', 'CACHE', 'RESUME', 'PRECALL', 'EXTENDED_ARG'):
            continue
        if ins.argrepr:
            c['%s %s' % (ins.opname, ins.argrepr)] += 1
        else:
            c[ins.opname] += 1
    return c


for rel, name in TARGETS:
    pyc = os.path.abspath(REPO + '/site-packages/' + rel.replace('/', os.sep))
    prod = pyc[:-4] + 'OK.py'
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    if name not in o or name not in d:
        print('%s :: %s  MISSING (o=%s d=%s)' % (rel, name, name in o, name in d))
        continue
    A, B = usage(o[name]), usage(d[name])
    lost = {k: A[k] - B.get(k, 0) for k in A if A[k] > B.get(k, 0)}
    gained = {k: B[k] - A.get(k, 0) for k in B if B[k] > A.get(k, 0)}
    tot_lost = sum(lost.values())
    print('== %s :: %s  instr %d -> %d ; operand-uses lost=%d gained=%d'
          % (rel.split('/')[-1], name.replace('<module>.', ''), len(o[name].co_codes)
             if hasattr(o[name], 'co_codes') else sum(A.values()), sum(B.values()),
             tot_lost, sum(gained.values())))
    for k, v in sorted(lost.items(), key=lambda kv: -kv[1])[:14]:
        print('   -%-3d %s' % (v, k[:86]))
    for k, v in sorted(gained.items(), key=lambda kv: -kv[1])[:6]:
        print('   +%d %s' % (v, k[:86]))
