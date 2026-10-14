"""Search plausible source texts for loop1's compound test for the one that reproduces the
original's jump SHAPE: entry legs PJIT(body), PJIT(body), PJIF(stub)->exit, PJT(exit),
then the two stub blocks JUMP_FORWARD(body) and JUMP_FORWARD(exit) immediately before the body.

usage: python -X utf8 work/shape_search.py
"""
import dis
import types

A = "int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading"
B = "int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)"
C = "holiday_sync_account == '0'"
D = "self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())"

TMPL = '''
def f(self, pre_before_trading, post_after_trading, holiday_sync_account, datetime, int, time, steps):
    while True:
        while %(COND)s:
            time.sleep(60)
        if %(D)s and self.reconnect_flag is False:
            system_log.debug('x')
            if not reconnect(self.broker.trade_account, self.trade_id):
                return
            self.reconnect_flag = True
        time.sleep(steps)
'''

CONDS = {
    'v1 A or B or (C and not D)': "%(A)s or %(B)s or (%(C)s and not %(D)s)",
    'v2 A or B or C and not D': "%(A)s or %(B)s or %(C)s and not %(D)s",
    'v3 A or B or (not D and C)': "%(A)s or %(B)s or (not %(D)s and %(C)s)",
    'v4 A or B or (C and D is False)': "%(A)s or %(B)s or (%(C)s and %(D)s is False)",
    'v5 (A or B) or (C and not D)': "(%(A)s or %(B)s) or (%(C)s and not %(D)s)",
    'v6 A or (B or (C and not D))': "%(A)s or (%(B)s or (%(C)s and not %(D)s))",
    'v7 A or B or not (D or not C)': "%(A)s or %(B)s or not (%(D)s or not %(C)s)",
    'v8 A or B or not (D or C != 0)': "%(A)s or %(B)s or not (%(D)s or holiday_sync_account != '0')",
}

TARGET = ['POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE',
          'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
          'JUMP_FORWARD', 'JUMP_FORWARD']


for name, tmpl in CONDS.items():
    cond = tmpl % dict(A=A, B=B, C=C, D=D)
    src = TMPL % dict(COND=cond, D=D)
    try:
        comp = compile(src, '<p>', 'exec')
    except SyntaxError as e:
        print('%-32s SYNTAX %s' % (name, e))
        continue
    co = [c for c in comp.co_consts if isinstance(c, types.CodeType) and c.co_name == 'f'][0]
    instrs = [i for i in dis.get_instructions(co) if i.opname not in ('NOP', 'CACHE', 'EXTENDED_ARG')]
    # entry chain = the first six conditional/unconditional forward jumps
    js = [i for i in instrs if i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                            'JUMP_FORWARD')][:6]
    seq = [i.opname.replace('POP_JUMP_FORWARD_', 'PJ_') for i in js]
    tg = [i.targets[0] if getattr(i, 'targets', None) else None for i in js]
    # body start = offset of the first LOAD_GLOBAL 'time' after the chain
    body = None
    exitb = None
    for i in instrs:
        if i.opname == 'LOAD_ATTR' and i.argrepr == 'sleep':
            body = i.offset - 6
            break
    for k, i in enumerate(instrs):
        if i.opname == 'LOAD_ATTR' and i.argrepr == 'is_trading_date' and k > 5:
            exitb = instrs[k - 1].offset
            break
    print('%-32s seq=%-88s body=%-6s exit=%-6s stubs=%d' % (
        name, ' '.join(seq), body, exitb,
        sum(1 for i in instrs if i.opname == 'JUMP_FORWARD')))
print('original  seq=PJ_IF_TRUE PJ_IF_TRUE PJ_IF_FALSE PJ_IF_TRUE JUMP_FORWARD JUMP_FORWARD'
      '  body=704   exit=1214  stubs=2 (@700 -> body, @702 -> exit)')
