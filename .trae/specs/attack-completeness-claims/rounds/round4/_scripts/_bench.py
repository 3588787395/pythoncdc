#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微基准：判据本体 evaluate 与 judge-visible signature 的耗时对比。"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
sys.path.insert(0, HERE)
import judge_sig  # noqa: E402

spec = importlib.util.spec_from_file_location('pv', os.path.join(ROOT, 'scripts', 'pyc_verify.py'))
pv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pv)

pycs = [
    os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness', 'rounds', 'round1', 'rec1_probes_r8matrix1.json'),
]

import json
items = []
d = json.load(open(pycs[0], encoding='utf-8'))
for r in d:
    if r.get('status') == 'success':
        items.append(r)
print('probe items:', len(items))

compare_pyc = pv.load_compare_pyc(pv.DEFAULT_PYLINGUAL)
file_sig = judge_sig.load_sig(pv.DEFAULT_PYLINGUAL)
tmp = tempfile.mkdtemp()
n = 10
t0 = time.time()
for r in items[:n]:
    prod = os.path.abspath(r['pyc_src_rel'].replace('/', os.sep))[:-4] + 'OK.py'
    if not os.path.isfile(prod):
        continue
    pv.evaluate(os.path.abspath(r['pyc_src_rel'].replace('/', os.sep)), prod, tmp, compare_pyc)
t1 = time.time()
print('judge evaluate: %.3f s/call' % ((t1 - t0) / max(1, n)))

t0 = time.time()
for r in items[:n]:
    p = os.path.abspath(r['pyc_src_rel'].replace('/', os.sep))
    if not os.path.isfile(p):
        continue
    file_sig(p)
t1 = time.time()
print('file_sig      : %.3f s/call' % ((t1 - t0) / max(1, n)))
