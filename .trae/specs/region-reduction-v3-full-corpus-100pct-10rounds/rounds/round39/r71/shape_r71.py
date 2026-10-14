import dis, marshal, types, sys
# Target: reproduce the compound-while shape and compare conditional-jump signature
orig_data = open(r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc','rb').read()
top = marshal.loads(orig_data[16:])
CO=types.CodeType
def find(c,name):
    for k in c.co_consts:
        if isinstance(k,CO):
            if k.co_name==name: return k
            r=find(k,name)
            if r: return r
    return None
mod=[k for k in top.co_consts if isinstance(k,CO) and k.co_name=='TradeLiveBroker'][0]
orig=find(mod,'_sync_worker')

def sig(co):
    out=[]
    for i in dis.get_instructions(co):
        if i.opname in ('POP_JUMP_FORWARD_IF_TRUE','POP_JUMP_FORWARD_IF_FALSE',
                        'POP_JUMP_BACKWARD_IF_TRUE','POP_JUMP_BACKWARD_IF_FALSE'):
            out.append((i.offset,i.opname,i.argval))
    return out
print("=== ORIGINAL compound-while conditional-jump signature ===")
for s in sig(orig): print(s)

# candidate source: only the while region, in a matching module context
cand = '''
import datetime
import time
pre_before_trading=0
post_after_trading=0
holiday_sync_account='0'
class D:
    def date(self,x): return x
    def is_trading_date(self,x): return x
class E:
    data_proxy=D()
class S:
    engine=None
    business_type='stock'
    order_or_trade_lock=None
    on_order_response_list=[]
    on_trade_response_list=[]
    def sync_account(self): pass
    def _sync_worker(self, engine):
        steps=1
        while True:
            while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
                   or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)
                   or (holiday_sync_account == '0'
                       and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()))):
                time.sleep(60)
            break
'''
ns={}
try:
    compile(cand,'<c>','exec')
except Exception as e:
    print("compile err",e)
cm=None
cmodule=compile(cand,'<c>','exec')
def find2(c,name):
    for k in c.co_consts:
        if isinstance(k,CO):
            if k.co_name==name: return k
            r=find2(k,name)
            if r: return r
    return None
cw=find2(cmodule,'_sync_worker')
print("=== CANDIDATE while-region conditional-jump signature ===")
ss=sig(cw)
for s in ss: print(s)
# normalize: check the sub-sequence of the compound while (offsets differ) by opcode pattern
op_pat=[(s[1]) for s in ss]
orig_pat=[(s[1]) for s in sig(orig)]
print("cand pat count",len(op_pat))
