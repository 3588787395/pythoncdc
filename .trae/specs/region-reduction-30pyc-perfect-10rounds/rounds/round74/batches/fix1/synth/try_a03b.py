# -*- coding: utf-8 -*-
"""Build synth a03 candidates from the real witness function
IQCommon/api/klinedata.pyc::get_multiminute_his_data (verbatim + trimmed),
then show which arm loses / keeps the function-tail statement."""
import difflib
import hashlib
import io
import os
import py_compile
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r74gate/center'
W = r'D:/Temp/opencode/r74gate/fix1/synth'

full = io.open(REPO + '/site-packages/IQCommon/api/klinedataOK.py', encoding='utf-8').read()
i = full.find('def get_multiminute_his_data')
FN = full[i:full.find('\ndef ', i + 5)].rstrip() + '\n'

HEAD = '''# synth a03 -- "merged child holds trailing statement".
# witness: IQCommon/api/klinedata.pyc::get_multiminute_his_data.
# expected: abs1 (analyzer same-target exemption) makes the top-level
# IfRegion swallow the merged child -> function-tail assignment lost;
# absj (abs1 + abs2 orphan-child emit) keeps it.
'''

CANDS = {
    'abs_a03_tail_after_topif': HEAD + FN,
    'abs_a03t_trim': HEAD + FN.replace(
        "        else:\n            add_fre_minute_time",
        "        else:\n            add_fre_minute_time").replace(
        "                    his_data_fix['open'][-1] = fix_data['open'][0].copy()\n"
        "                    his_data_fix['high'][-1] = fix_data['high'].max().copy()\n"
        "                    his_data_fix['low'][-1] = fix_data['low'].min().copy()\n"
        "                    his_data_fix['close'][-1] = fix_data['close'][-1].copy()\n"
        "                    his_data_fix['volume'][-1] = fix_data['volume'].sum().copy()\n"
        "                    his_data_fix['money'][-1] = fix_data['money'].sum().copy()\n"
        "                    his_data_fix['price'][-1] = fix_data['price'][-1].copy()\n", ""),
}

TAIL = 'his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include, execution_date, asset, dividends_all)'

sys.path.insert(0, GATE)
import h62  # noqa: E402

ARMS = ('landed', 'abs1', 'abs2', 'absj')


def load(arm):
    for m in [k for k in list(sys.modules)
              if k == 'pycdc' or k == 'core' or k.startswith('core.')]:
        del sys.modules[m]
    for m in [k for k, mod in list(sys.modules.items())
              if getattr(mod, '__file__', None)
              and os.path.abspath(mod.__file__).replace('\\', '/').startswith(GATE)]:
        del sys.modules[m]
    sys.path = [x for x in sys.path if not os.path.abspath(x).replace('\\', '/').startswith(GATE)]
    return h62._load_arm(arm)


PYCS = []
for name, src in CANDS.items():
    p = os.path.join(W, name + '.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(src)
    py_compile.compile(p, cfile=os.path.join(W, name + '.pyc'), doraise=True)
    PYCS.append((name, os.path.join(W, name + '.pyc')))
    print('compiled', name, len(src.splitlines()), 'lines')

for name, pyc in PYCS:
    prods = {}
    for arm in ARMS:
        pycdc = load(arm)
        dst = os.path.join(GATE, 'build_' + arm, name + 'OK.py')
        text = pycdc.decompile_pyc(pyc)
        io.open(dst, 'w', encoding='utf-8', newline='\n').write(text)
        prods[arm] = text
    print('== %s' % name)
    for arm in ARMS:
        fn = prods[arm]
        s = fn.find('def get_multiminute_his_data')
        seg = fn[s:fn.find('\ndef ', s + 5)] if s >= 0 else ''
        print('   %-7s sha16=%s tail=%d' % (
            arm, hashlib.sha256(prods[arm].encode()).hexdigest()[:16], seg.count(TAIL)))
    print('   landed==abs1 %s | landed==absj %s | abs1==absj %s' % (
        prods['landed'] == prods['abs1'], prods['landed'] == prods['absj'],
        prods['abs1'] == prods['absj']))
    if prods['abs1'] != prods['absj']:
        print('   --- abs1 vs absj diff ---')
        print('\n'.join('   ' + x for x in list(difflib.unified_diff(
            prods['abs1'].splitlines(), prods['absj'].splitlines(), lineterm='', n=1))[:60]))
