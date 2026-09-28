# -*- coding: utf-8 -*-
import io
import os
import py_compile
import sys

sys.stdout.reconfigure(encoding='utf-8')
W = r'D:/Temp/opencode/r74gate/fix1/synth'

srcs = {}
srcs['abs_a03_tail_after_topif'] = '''# synth a03 -- "merged child holds trailing statement": shape taken from
# IQCommon/api/klinedata.pyc::get_multiminute_his_data (top-level if that
# returns early, shared/merged child region, function tail statement after it).
# expected: landed / abs1 skip the skipped child -> trailing statement lost;
# absj emits it -> statement survives (mandated failure -> success).
def synth_a03_tail_after_topif(symbols, count, include, query_date, close, frequency='1d'):
    his_data_dict = {}
    if include and query_date > 100:
        if count == 0:
            his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency)
            if len(his_data_dict) == 0:
                return his_data_dict
        else:
            fix_data = get_kline_by_count(symbols, count, query_date, '1m')
            if len(fix_data) == 0:
                return his_data_dict
            his_data_dict['fix'] = fix_data
        return his_data_dict
    his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency)
    return his_data_dict


def get_kline_by_count_new(symbols, count, query_date, frequency):
    return {'n': (symbols, count, query_date, frequency)}


def get_kline_by_count(symbols, count, query_date, frequency):
    return {'m': (symbols, count, query_date, frequency)}
'''
srcs['abs_a03b_shared_else_tail'] = '''# synth a03b -- shared else + trailing statement inside merged child.
def synth_a03b_shared_else_tail(a, b, c, d):
    out = 0
    if a and b > c:
        if not b:
            if c <= d:
                x = 1
            else:
                x = 2
        else:
            x = 3
        out = x + c
    else:
        out = -1
    tail = get_tail(out, a, b, c, d)
    return tail


def get_tail(out, a, b, c, d):
    return out * (a + b + c + d)
'''
srcs['abs_a03c_elif_chain_tail'] = '''# synth a03c -- elif chain shared tail holding a trailing statement.
def synth_a03c_elif_chain_tail(flag, value, a, b, c):
    if flag == 1:
        data = 1
    elif flag == -1:
        data = -1
    else:
        data = 0
    his_data = load_his(value, a, b, c, data)
    return his_data


def load_his(value, a, b, c, data):
    return (value, a, b, c, data)
'''

for k, v in sorted(srcs.items()):
    p = os.path.join(W, k + '.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(v)
    py_compile.compile(p, cfile=p[:-3] + '.pyc', doraise=True)
    print('wrote', k, os.path.getsize(p) , os.path.getsize(p + 'c'))
