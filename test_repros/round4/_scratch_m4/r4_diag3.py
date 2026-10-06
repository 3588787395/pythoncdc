import sys, marshal, dis
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
_orig = RegionAnalyzer._find_try_else_blocks
def patched(self, tr):
    r = _orig(self, tr)
    print('    [find_try_else] entry', tr.entry.start_offset if tr.entry else None, 'try_end', getattr(tr,'try_offset_end',None), '->', [b.start_offset for b in r])
    return r
RegionAnalyzer._find_try_else_blocks = patched

path = sys.argv[1]
f = open(path, 'rb'); f.read(16); co = marshal.load(f)
targets = sys.argv[2:]
for c in co.co_consts:
    if not hasattr(c, 'co_code'):
        continue
    if targets and c.co_name not in targets:
        continue
    print('##########', c.co_name)
    print(dis.Bytecode(c).exception_entries)
    cb = CFGBuilder(); cfg = cb.build(c)
    an = RegionAnalyzer(cfg); an.analyze()
    for hi in an.handler_infos:
        print('  HINFO', hi)
    for r in an.regions:
        rt = getattr(r.region_type, 'name', r.region_type)
        print('  REGION', rt, 'entry', r.entry.start_offset if r.entry else None,
              'blocks', [b.start_offset for b in r.blocks])