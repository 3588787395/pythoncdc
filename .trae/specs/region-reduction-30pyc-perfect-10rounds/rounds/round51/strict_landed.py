# -*- coding: utf-8 -*-
"""Strict per-function re-check of the LANDED products already built by run --arm=landed.

usage: python -X utf8 strict_landed.py   (prints per-file strict matched/total + defects)
"""
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BUILD = r'D:/Temp/r51b/build_landed'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r51sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

REL = ['IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc',
       'fly/data/quotation.pyc',
       'fly/data/quote_handler.pyc',
       'IQCommon/api/klinedata.pyc',
       'IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc']
for rel in REL:
    pyc = os.path.join(REPO, 'site-packages', rel.replace('/', os.sep))
    prod = os.path.join(BUILD, rel.replace('/', '__')[:-4] + 'OK.py').replace('\\', '/')
    if not os.path.exists(prod):
        print('MISSING %s' % prod)
        continue
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    bad = []
    n = 0
    for name in sorted(set(o) & set(d)):
        n += 1
        kind, msg, isdef = r10.strict_compare(o[name], d[name])
        if isdef:
            bad.append('%s [%s] %s' % (name.split('.')[-1][:30], kind, msg))
    print('%-62s %3d/%-3d' % (rel[-62:], n - len(bad), n))
    for b in bad:
        print('    ' + b)
