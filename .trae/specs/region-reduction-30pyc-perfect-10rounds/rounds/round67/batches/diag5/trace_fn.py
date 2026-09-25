# -*- coding: utf-8 -*-
"""Line-trace the Nth call of a target function while decompiling one pyc.

usage: python -X utf8 trace_fn.py <arm> <pyc> <funcname> [which]
"""
import sys, os, io, collections
sys.path.insert(0, '.')
import h62

arm, pyc, want = sys.argv[1], sys.argv[2], sys.argv[3]
which = int(sys.argv[4]) if len(sys.argv) > 4 else 1
pycdc = h62._load_arm(arm)
calls = []
cur = {'n': 0, 'log': []}


def make_local(idx):
    def local(frame, event, arg):
        if idx != which:
            return None
        if event == 'line':
            cur['log'].append(('L', frame.f_lineno))
        elif event == 'return':
            cur['log'].append(('RET', frame.f_lineno, repr(arg)[:400]))
        elif event == 'call':
            if frame.f_code.co_name in ('_generate_ternary', '_r63b3_reduce_value_ctx_chain_store'):
                return None
        return local
    return local


def tr(frame, event, arg):
    if event == 'call':
        if frame.f_code.co_name == want:
            n = len(calls) + 1
            calls.append(n)
            if n == which:
                return make_local(n)
        return tr
    return tr


sys.settrace(tr)
out = pycdc.decompile_pyc(pyc)
sys.settrace(None)
io.open('trace_fn.txt', 'w', encoding='utf-8').write(
    'calls=%d\n' % len(calls) + '\n'.join(map(str, cur['log'])) + '\n---OUT---\n' + out)
print('calls to %s: %d ; traced %d lines' % (want, len(calls), len(cur['log'])))
print(out)
