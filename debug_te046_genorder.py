import sys, os
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.cfg_builder import CFGBuilder
import core.cfg.region_ast_generator as rag_mod

src = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
code = compile(src, '<t>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

gen_cls = rag_mod.RegionASTGenerator
orig_generate_region = gen_cls._generate_region

def traced_generate_region(self, region):
    rt = getattr(region, 'region_type', None)
    e = getattr(region, 'entry', None)
    eoff = e.start_offset if e is not None else None
    # Check if entry block already generated
    already = e in self.generated_blocks if e is not None else False
    result = orig_generate_region(self, region)
    # Truncate result for printing
    res_summary = repr(result)
    if len(res_summary) > 300:
        res_summary = res_summary[:300] + "..."
    print(f"  [GEN] _generate_region({type(region).__name__} entry={eoff} rt={rt}) already_gen={already} -> {res_summary}")
    return result

gen_cls._generate_region = traced_generate_region

gen = rag_mod.RegionASTGenerator(cfg, analyzer)
ast_dict = gen.generate()

print()
print("==== generated_blocks (offsets) ====")
print(sorted([b.start_offset for b in gen.generated_blocks]))
print()
print("==== Are 158 and 206 in generated_blocks? ====")
for off in [158, 206, 202, 228, 240]:
    blk = None
    for b in cfg.blocks.values():
        if b.start_offset == off:
            blk = b
            break
    if blk:
        print(f"  block {off}: in generated_blocks = {blk in gen.generated_blocks}")
