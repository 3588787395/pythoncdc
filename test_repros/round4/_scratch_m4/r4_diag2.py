import sys, marshal
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg import region_analyzer as RA
from core.cfg.region_analyzer import RegionAnalyzer

path = sys.argv[1]
f = open(path, 'rb'); f.read(16); co = marshal.load(f)
targets = sys.argv[2:]

_orig = RA.RegionAnalyzer._follow_except_chain
def patched(self, handler_entry):
    res = _orig(self, handler_entry)
    print('    [follow_except_chain] entry', handler_entry.start_offset, '-> handlers', len(res[0]), 'entries', [b.start_offset for b in res[1]])
    return res
RA.RegionAnalyzer._follow_except_chain = patched

for c in co.co_consts:
    if not hasattr(c, 'co_code'):
        continue
    if targets and c.co_name not in targets:
        continue
    print('##########', c.co_name)
    cb = CFGBuilder(); cfg = cb.build(c)
    an = RegionAnalyzer(cfg); an.analyze()
    for b in cfg.get_blocks_in_order():
        print('   BLK', b.start_offset, [i.opname for i in b.instructions], 'succ', [s.start_offset for s in b.successors], 'exc', [s.start_offset for s in b.exception_successors])