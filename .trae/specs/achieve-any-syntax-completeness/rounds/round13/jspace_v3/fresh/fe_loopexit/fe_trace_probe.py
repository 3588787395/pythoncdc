import sys, types, traceback
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import core.cfg.region_analyzer as ra
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

src = open(r'D:\temp\opencode\cl_layout\fe\fe_variants.py', encoding='utf-8').read()
code = compile(src, '<f>', 'exec')
fnc = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name=='m3'][0]
cfg = build_cfg(fnc, name='m3')

class TraceSet(set):
    def __init__(self, it=(), tag=''):
        super().__init__(it)
        self.tag = tag
    def add(self, item):
        st = traceback.extract_stack()[-4:-1]
        caller = ' <- '.join(f'{f.name}:{f.lineno}' for f in reversed(st))
        print(f'[ADD loop.blocks] B{getattr(item,"id","?")} via {caller}')
        super().add(item)

orig_ident_loops = ra.RegionAnalyzer._identify_loop_regions
def patched(self):
    regions = orig_ident_loops(self)
    for r in regions:
        if isinstance(r, LoopRegion):
            b7 = self.cfg.get_block_by_offset(104)
            print(f'[after _identify_loop_regions] loop blocks contains B7: {b7 in r.blocks}; blocks={sorted(b.id for b in r.blocks)}; block_to_region B7 -> {type(self.block_to_region.get(b7)).__name__ if self.block_to_region.get(b7) else None}')
            r.blocks = TraceSet(r.blocks, tag=f'loop@{r.header_block.id}')
    return regions
ra.RegionAnalyzer._identify_loop_regions = patched

an = RegionAnalyzer(cfg, parent_code=fnc)
regions = an.analyze()
b7 = cfg.get_block_by_offset(104)
loop = [r for r in regions if isinstance(r, LoopRegion)][0]
print('FINAL: B7 in loop.blocks =', b7 in loop.blocks)
print('block_to_region B7 ->', an.block_to_region.get(b7))
