# -*- coding: utf-8 -*-
"""a03 candidate sweep: look for a shape where the merged child holds a
trailing statement that landed/abs1 drop and absj keeps."""
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

CANDS = {}

CANDS['abs_a03q_shared_tail_return'] = '''# synth a03q -- merged child holds trailing statement (shape from
# fly/data/quote.pyc::get_real_from_zeromq flag ladder).
# expected: landed / abs1 inline `return None` into each branch and drop the
# shared `return None, flag` tail; absj emits the merged child -> tail kept.
def synth_a03q_shared_tail_return(redata, flag, log):
    if not redata:
        if flag == 1:
            log.info('real数据转化异常，默认返回空值')
        elif flag == -1:
            log.info('real数据返回空值')
        return None, flag
    return redata
'''

CANDS['abs_a03r_tail_after_boolop_if'] = '''# synth a03r -- top-level `if A and B:` with for/continue sink, tail
# assignment after the if (klinedata witness shape, trimmed).
def synth_a03r_tail_after_boolop_if(symbols, count, query_date, frequency, include, fields=None, fq=None):
    his_data_dict = {}
    if include and query_date > 100:
        count_min = 0
        if count == 0:
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

CANDS['abs_a03s_nested_else_shared_tail'] = '''# synth a03s -- nested if/else inside top-level if, shared tail statement
# after the inner chain, function-tail assignment after the outer if.
def synth_a03s_nested_else_shared_tail(a, b, c, d, log):
    out = {}
    if a and b > c:
        if not b:
            if c <= d:
                out['x'] = 1
            else:
                out['x'] = 2
        else:
            out['x'] = 3
        return out
    out = get_tail(a, b, c, d, log)
    return out


def get_tail(a, b, c, d, log):
    return {'t': (a, b, c, d)}
'''

ARMS = ('landed', 'abs1', 'abs2', 'absj')


def load(arm):
    for m in [k for k in list(sys.modules)
              if k == 'pycdc' or k == 'core' or k.startswith('core.')]:
        del sys.modules[m]
    for m in [k for k, mod in list(sys.modules.items())
              if getattr(mod, '__file__', None)
              and os.path.abspath(mod.__file__).replace('\\', '/').startswith(GATE)]:
        del sys.modules[m]
    sys.path = [x for x in sys.path
                if not os.path.abspath(x).replace('\\', '/').startswith(GATE)]
    return h62._load_arm(arm)


sys.path.insert(0, GATE)
import h62  # noqa: E402

for name, src in sorted(CANDS.items()):
    p = os.path.join(W, name + '.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(src)
    py_compile.compile(p, cfile=os.path.join(W, name + '.pyc'), doraise=True)
    prods = {}
    for arm in ARMS:
        text = load(arm).decompile_pyc(os.path.join(W, name + '.pyc'))
        io.open(os.path.join(GATE, 'build_' + arm, name + 'OK.py'),
                'w', encoding='utf-8', newline='\n').write(text)
        prods[arm] = text
    print('== %s  landed==abs1 %s landed==absj %s abs1==absj %s' % (
        name, prods['landed'] == prods['abs1'],
        prods['landed'] == prods['absj'], prods['abs1'] == prods['absj']))
    if prods['abs1'] != prods['absj']:
        print('   --- abs1 vs absj ---')
        print('\n'.join('   ' + x for x in list(difflib.unified_diff(
            prods['abs1'].splitlines(), prods['absj'].splitlines(), lineterm='', n=1))[:40]))
    if prods['landed'] != prods['absj']:
        print('   --- landed vs absj ---')
        print('\n'.join('   ' + x for x in list(difflib.unified_diff(
            prods['landed'].splitlines(), prods['absj'].splitlines(), lineterm='', n=1))[:40]))
