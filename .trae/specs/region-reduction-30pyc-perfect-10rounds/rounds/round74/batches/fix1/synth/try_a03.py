# -*- coding: utf-8 -*-
import difflib
import hashlib
import io
import os
import py_compile
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r74gate/center'
W = r'D:/Temp/opencode/r74gate/fix1/synth'

SRC = '''# synth a03 -- "merged child holds trailing statement".
# shape taken from IQCommon/api/klinedata.pyc::get_multiminute_his_data:
# top-level `if A and B:` whose body has an elif chain + a for/continue sink
# and early returns, then a function-tail assignment before the final return.
# landed / abs1 skip the merged child region -> tail assignment lost;
# absj emits the child -> statement survives.
def synth_a03_tail_after_topif(symbols, count, query_date, frequency, include, fields=None, fq=None):
    his_data_dict = {}
    if include and query_date > 100:
        count_min = 0
        query_time = str(query_date)
        if query_time[8:12] <= '1130':
            count_min = 1
        elif query_time[8:12] <= '1500':
            count_min = 2
        if count_min == 0:
            his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include)
            if len(his_data_dict) == 0:
                return his_data_dict
        else:
            for symbol in symbols:
                his = get_kline_by_count(symbol, count, query_date, '1m')
                if len(his) == 0:
                    continue
                his_data_dict[symbol] = his
                continue
        return his_data_dict
    his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include)
    return his_data_dict


def get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include):
    return {'n': (symbols, count, query_date, frequency, fields, fq, include)}


def get_kline_by_count(symbol, count, query_date, frequency):
    return {'m': (symbol, count, query_date, frequency)}
'''

NAME = 'abs_a03_tail_after_topif'
p = os.path.join(W, NAME + '.py')
io.open(p, 'w', encoding='utf-8', newline='\n').write(SRC)
py_compile.compile(p, cfile=os.path.join(W, NAME + '.pyc'), doraise=True)
PYC = os.path.join(W, NAME + '.pyc')
print('compiled', NAME)

sys.path.insert(0, GATE)
import h62  # noqa: E402

TAIL = 'his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include)'
prods = {}
for arm in ('landed', 'abs1', 'abs2', 'absj'):
    for m in [k for k in list(sys.modules)
              if k == 'pycdc' or k == 'core' or k.startswith('core.')]:
        del sys.modules[m]
    for m in [k for k, mod in list(sys.modules.items())
              if getattr(mod, '__file__', None)
              and os.path.abspath(mod.__file__).replace('\\', '/').startswith(GATE)]:
        del sys.modules[m]
    sys.path = [x for x in sys.path if not os.path.abspath(x).replace('\\', '/').startswith(GATE)]
    pycdc = h62._load_arm(arm)
    os.makedirs(GATE + '/build_' + arm, exist_ok=True)
    dst = os.path.join(GATE + '/build_' + arm, NAME + 'OK.py')
    text = pycdc.decompile_pyc(PYC)
    io.open(dst, 'w', encoding='utf-8', newline='\n').write(text)
    prods[arm] = text
    fn = text[text.find('def synth_a03'):text.find('\ndef ', text.find('def synth_a03') + 5)]
    print('%-7s sha16=%s tail_stmts_in_fn=%d' % (
        arm, hashlib.sha256(text.encode('utf-8')).hexdigest()[:16], fn.count(TAIL)))

print('landed==abs1', prods['landed'] == prods['abs1'],
      '| landed==absj', prods['landed'] == prods['absj'],
      '| abs1==absj', prods['abs1'] == prods['absj'])
if prods['landed'] != prods['absj']:
    print('--- diff landed vs absj ---')
    print('\n'.join(list(difflib.unified_diff(
        prods['landed'].splitlines(), prods['absj'].splitlines(),
        lineterm='', n=1))[:60]))
