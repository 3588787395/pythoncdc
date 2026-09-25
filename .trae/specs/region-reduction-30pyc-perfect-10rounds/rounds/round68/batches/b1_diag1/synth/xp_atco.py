# -*- coding: utf-8 -*-
"""diag1 r68 experiment: is `after_trading_cancel_order` an elif over-merge?

Compiles N hand-written variants of the function and diffs each one's
instruction stream against the ORIGINAL code object from the target pyc.
"""
import dis
import io
import marshal
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
LAND_OK = 'build_landed/IQEngine__plugins__plugin_system_trade__trade_live_brokerOK.py'
FUNC = 'after_trading_cancel_order'
HEAD = '''class _L(object):
    def warning(self, m): pass
    def error(self, m): pass
    def info(self, m): pass
strategy_log = _L()
_ = lambda s: s
class _AC(object):
    def __getitem__(self, k): pass
    def __setitem__(self, k, v): pass
class _BK(object):
    trade_account = None
EXCHANGE_TYPES_DICT = {}


class TradeLiveBroker(object):
'''
BODY_LANDED = '''    def after_trading_cancel_order(self, order_param):
        if order_param is None:
            strategy_log.warning(_('x'))
            return None
        elif isinstance(order_param, str):
            for order in self.after_trading_orders:
                if order_param == order.order_id:
                    order_param = order
                    break
        elif isinstance(order_param, str):
            return None
        else:
            entrust_no = order_param.entrust_no
            return None
'''
BODY_SEQ = '''    def after_trading_cancel_order(self, order_param):
        if order_param is None:
            strategy_log.warning(_('x'))
            return None
        elif isinstance(order_param, str):
            for order in self.after_trading_orders:
                if order_param == order.order_id:
                    order_param = order
                    break
        if isinstance(order_param, str):
            return None
        else:
            entrust_no = order_param.entrust_no
            return None
'''
BODY_NESTED_ELSE = '''    def after_trading_cancel_order(self, order_param):
        if order_param is None:
            strategy_log.warning(_('x'))
            return None
        elif isinstance(order_param, str):
            for order in self.after_trading_orders:
                if order_param == order.order_id:
                    order_param = order
                    break
        else:
            if isinstance(order_param, str):
                return None
            else:
                entrust_no = order_param.entrust_no
                return None
'''


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def stream(c):
    return ['%s %s' % (i.opname, i.argrepr) for i in dis.get_instructions(c)
            if i.opname != 'CACHE']


def find(root, name):
    return [c for c in walk(root, []) if c.co_name == name][0]


def get_instructions_count(c):
    return len(stream(c))


orig_code = find(marshal.loads(io.open(PYC, 'rb').read()[16:]), FUNC)
orig = stream(orig_code)
print('ORIG count=%d' % len(orig))
print('orig[28:40]=%s' % (orig[28:40],))

variants = {'landed-shape': BODY_LANDED, 'sequential-if': BODY_SEQ,
            'nested-else': BODY_NESTED_ELSE}
for nm, body in variants.items():
    src = HEAD + body
    try:
        root = compile(src, '<v>', 'exec')
    except SyntaxError as e:
        print('%-14s SYNTAX %s' % (nm, e))
        continue
    c = find(root, FUNC)
    s = stream(c)
    same = sum(1 for x, y in zip(orig, s) if x == y)
    print('%-14s count=%-4d common_prefix_run=%d  first_diff_idx=%s'
          % (nm, len(s), same,
             next((k for k in range(min(len(orig), len(s))) if orig[k] != s[k]),
                  min(len(orig), len(s)))))
    k = next((k for k in range(min(len(orig), len(s))) if orig[k] != s[k]), None)
    if k is not None:
        print('     orig[%d:%d]=%s' % (k, k + 6, orig[k:k + 6]))
        print('     var [%d:%d]=%s' % (k, k + 6, s[k:k + 6]))
