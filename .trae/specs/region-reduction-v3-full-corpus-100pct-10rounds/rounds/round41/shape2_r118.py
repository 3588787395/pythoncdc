import dis,sys
from bcore_r118 import blocks
HEAD='''
def f(self, dt, EventEnum, system_log, now_date, holiday_not_do_before, FPS):
    while True:
'''
TAIL='''
        break
'''
HOISTED=HEAD+'''
        if holiday_not_do_before == '0':
            self.event_queue.put((dt, EventEnum.BEFORE_TRADING_START))
        self.before_trading_date = now_date
        time.sleep(FPS)
        continue
'''+TAIL
ELSEBODY=HEAD+'''
        if holiday_not_do_before == '0':
            self.event_queue.put((dt, EventEnum.BEFORE_TRADING_START))
        else:
            self.before_trading_date = now_date
        time.sleep(FPS)
        continue
'''+TAIL
for nm,src in (('HOISTED(as-ours)',HOISTED),('ELSE-BODY(as-orig)',ELSEBODY)):
    co=[k for k in compile(src,'<t>','exec').co_consts if getattr(k,'co_name','')=='f'][0]
    bs=blocks(co)
    tag=[b for b in bs if 'STORE_ATTR' in b['sig']]
    slp=[b for b in bs if 'JUMP_BACKWARD' in b['sig'] and 'CALL' in b['sig']]
    print('%-20s blocks=%d instrs=%d' % (nm,len(bs),sum(b['n'] for b in bs)))
    for b in tag: print('   STORE_ATTR block line=%s n=%d in=%d out=%d sig=%s'%(b['line'],b['n'],b['in'],b['out'],b['sig']))
    for b in slp: print('   sleep+back  block line=%s n=%d in=%d out=%d'%(b['line'],b['n'],b['in'],b['out']))
