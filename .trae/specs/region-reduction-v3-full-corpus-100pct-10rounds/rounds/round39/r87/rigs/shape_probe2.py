"""Compile loop1 inside a `while True` (matching the original context) and report whether the
entry-chain threading JUMP_FORWARD stubs (@700/@702) appear as in the original pyc.
"""
import dis
import sys

VARIANTS = {
    'plain': '''
def f(self, pre_before_trading, post_after_trading, holiday_sync_account, datetime, int, time):
    while True:
        while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
               or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)
               or holiday_sync_account == '0'
               and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())):
            time.sleep(60)
        self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())
        if self.reconnect_flag is False:
            return None
''',
    'parens': '''
def f(self, pre_before_trading, post_after_trading, holiday_sync_account, datetime, int, time):
    while True:
        while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
               or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)
               or (holiday_sync_account == '0'
                   and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()))):
            time.sleep(60)
        self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())
        if self.reconnect_flag is False:
            return None
''',
    'swap': '''
def f(self, pre_before_trading, post_after_trading, holiday_sync_account, datetime, int, time):
    while True:
        while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
               or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)
               or (holiday_sync_account == '0'
                   and self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()) is False)):
            time.sleep(60)
        self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())
        if self.reconnect_flag is False:
            return None
''',
}

for name, src in VARIANTS.items():
    co = [c for c in compile(src, '<p>', 'exec').co_consts
          if isinstance(c, type(co := None) if False else type(compile('', '<>', 'exec'))) and c.co_name == 'f'][0]
    kept = [i for i in dis.get_instructions(co) if i.opname not in ('NOP', 'CACHE', 'EXTENDED_ARG')]
    ops = [i.opname for i in kept]
    print('===', name, 'n=', len(kept),
          'JUMP_FORWARD x2 near test =', ops.count('JUMP_FORWARD'))
    # print only the conditional jumps and plain jumps with target offsets
    for i in kept:
        if i.opname.startswith('POP_JUMP') or i.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
            tg = list(getattr(i, 'targets', None) or [])
            print('   @%-6d %-28s %s -> %s' % (i.offset, i.opname, i.argrepr or '', tg))
