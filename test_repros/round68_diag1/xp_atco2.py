# -*- coding: utf-8 -*-
"""diag1 r68: seam experiment on the REAL landed text of after_trading_cancel_order.

Extracts lines 2510..2537 from build_landed/...OK.py, rebuilds three variants that
differ ONLY at the elif-chain seam, compiles each and diffs the instruction stream
against the original code object.
"""
import dis
import io
import marshal
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
OK = 'build_landed/IQEngine__plugins__plugin_system_trade__trade_live_brokerOK.py'
LO, HI = 2510, 2537           # 1-based, inclusive


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def stream(c):
    return ['%s %s' % (i.opname, i.argrepr) for i in dis.get_instructions(c)
            if i.opname != 'CACHE']


lines = io.open(OK, encoding='utf-8').read().replace('\r\n', '\n').splitlines()
fn = lines[LO - 1:HI]
assert fn[0].strip().startswith('def after_trading_cancel_order'), fn[0]


def wrap(body):
    return 'class TradeLiveBroker(object):\n' + '\n'.join(body) + '\n'


def seam_split(b):
    out = []
    for i, l in enumerate(b):
        if i > 0 and l.strip().startswith('elif isinstance(order_param, str)') \
                and 'return' in b[i + 1]:
            out.append(l.replace('elif', 'if'))
        else:
            out.append(l)
    return out


def nested_else(b):
    out = []
    k = None
    for i, l in enumerate(b):
        if i > 0 and l.strip().startswith('elif isinstance(order_param, str)') \
                and 'return' in b[i + 1]:
            k = i
            break
    ind = len(b[k]) - len(b[k].lstrip())
    out = b[:k]
    out.append(' ' * ind + 'else:')
    tail = b[k].replace('elif', 'if', 1)
    out.append('    ' + tail)
    for l in b[k + 1:]:
        out.append(('    ' + l) if l.strip() else l)
    return out


variants = [('V0 landed as-is', fn), ('V1 seam -> sequential if', seam_split(fn)),
            ('V2 else: nested if', nested_else(fn))]

orig_code = [c for c in walk(marshal.loads(io.open(PYC, 'rb').read()[16:]), [])
             if c.co_name == 'after_trading_cancel_order'][0]
orig = stream(orig_code)
# jump targets are offsets of THIS code object; compare opname+argval+arg to be safe
orig_key = ['%s|%s|%s' % (i.opname, i.arg, i.argval)
            for i in dis.get_instructions(orig_code) if i.opname != 'CACHE']
print('ORIG instrs=%d' % len(orig_key))

for nm, body in variants:
    src = wrap(body)
    try:
        root = compile(src, '<v>', 'exec')
    except SyntaxError as e:
        print('%-26s SYNTAX ERROR %s' % (nm, e))
        continue
    c = [x for x in walk(root, []) if x.co_name == 'after_trading_cancel_order'][0]
    s = ['%s|%s|%s' % (i.opname, i.arg, i.argval)
         for i in dis.get_instructions(c) if i.opname != 'CACHE']
    k = next((j for j in range(min(len(orig_key), len(s))) if orig_key[j] != s[j]),
             min(len(orig_key), len(s)))
    print('%-26s instrs=%-4d equal_prefix=%-4d  IDENTICAL=%s'
          % (nm, len(s), k, k == len(orig_key) == len(s)))
    if k < len(orig_key) or len(s) != len(orig_key):
        print('     orig[%d:%d]=%s' % (k, k + 5, orig_key[k:k + 5]))
        print('     var [%d:%d]=%s' % (k, k + 5, s[k:k + 5]))
