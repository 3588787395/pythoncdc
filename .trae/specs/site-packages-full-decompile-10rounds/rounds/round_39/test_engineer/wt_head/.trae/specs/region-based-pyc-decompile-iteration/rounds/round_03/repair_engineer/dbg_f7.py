import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

src = '''class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()
'''
code = compile(src, '<dbg>', 'exec')

def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r:
                return r
    return None

init = find_code(code, '__init__')
print("init found:", init)
cfg = build_cfg(init)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

def dump(r, depth=0):
    pre = '  '*depth
    name = getattr(r, 'region_type', type(r).__name__)
    entry = getattr(r, 'entry', None)
    ei = entry.start_offset if (entry is not None and hasattr(entry,'index')) else entry
    blocks = getattr(r, 'blocks', set())
    bi = ','.join(str(b.start_offset) for b in sorted(blocks, key=lambda x: getattr(x,'index',0)))
    # print attributes of interest
    extra = ''
    for attr in ('value_target','merge_context','container_type','merge_block','condition_block','true_value_block','false_value_block'):
        if hasattr(r, attr):
            v = getattr(r, attr)
            if v is not None:
                vi = v.start_offset if hasattr(v,'index') else v
                extra += f' {attr}={vi}'
    print(f"{pre}[{name}] entry={ei} blocks={{{bi}}}{extra}")
    for sub in getattr(r, 'sub_regions', []) or []:
        dump(sub, depth+1)
    # children referenced via body/then/else
    for attr in ('body','then_blocks','else_blocks','then_body','else_body'):
        subs = getattr(r, attr, None)
        if isinstance(subs, (list,tuple)):
            for s in subs:
                if hasattr(s,'region_type'):
                    dump(s, depth+1)

for r in regions:
    dump(r)
print("=== block_to_region ===")
for b, r in sorted(analyzer.block_to_region.items(), key=lambda kv: kv[0].start_offset):
    rn = getattr(r,'region_type', type(r).__name__)
    re = getattr(r,'entry',None)
    ei = re.start_offset if (re is not None and hasattr(re,'index')) else re
    print(f"block {b.start_offset} -> [{rn}] entry={ei}")
