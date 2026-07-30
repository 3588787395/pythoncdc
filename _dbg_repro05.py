import sys, marshal, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

pyc = '/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_25/test_engineer/minimal_repros/repro_05_buildfuture_minimal_else_forloop.pyc'
with open(pyc, 'rb') as f:
    f.read(16); co = marshal.load(f)

fco = None
for c in co.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'f':
        fco = c; break

from core.cfg.cfg_builder import build_cfg
cfg = build_cfg(fco)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== REGIONS ===")
for r in analyzer.regions:
    rt = r.region_type.name if hasattr(r,'region_type') else type(r).__name__
    entry = r.entry.start_offset if getattr(r,'entry',None) else None
    blocks = sorted(b.start_offset for b in r.blocks) if hasattr(r,'blocks') else []
    extra = ''
    if hasattr(r,'elif_conditions') and r.elif_conditions:
        extra = f" elif_conds={[c.start_offset for c in r.elif_conditions]} elif_bodies={[[b.start_offset for b in eb] for eb in (r.elif_bodies or [])]} elif_final_else={[b.start_offset for b in (r.elif_final_else or [])]}"
    if hasattr(r,'then_blocks'):
        extra += f" then={[b.start_offset for b in r.then_blocks]} else={[b.start_offset for b in (r.else_blocks or [])]} merge={r.merge_block.start_offset if r.merge_block else None}"
    print(f"{type(r).__name__} rt={rt} entry={entry} blocks={blocks}{extra}")

print("\n=== block_to_region ===")
for b in cfg.get_blocks_in_order():
    br = analyzer.block_to_region.get(b)
    print(f"  block {b.start_offset}: {type(br).__name__ if br else None} entry={br.entry.start_offset if br and getattr(br,'entry',None) else None}")

print("\n=== children of each IfRegion ===")
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion':
        ch = [(type(c).__name__, c.entry.start_offset if getattr(c,'entry',None) else None) for c in getattr(r,'children',[])]
        print(f"  IfRegion@{r.entry.start_offset if r.entry else None} children={ch}")

print("\n=== AST GEN ===")
from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg, top_level_code=None)
import json
def dump(d, indent=0):
    pad = '  '*indent
    if isinstance(d, dict):
        t = d.get('type','?')
        keys = {k:v for k,v in d.items() if k not in ('type',)}
        print(f"{pad}{t} { {k:(v if not isinstance(v,(dict,list)) else '...') for k,v in keys.items()} }")
        if 'test' in d: dump(d['test'], indent+1)
        if 'body' in d:
            for s in d['body']: dump(s, indent+1)
        if 'orelse' in d and d['orelse']:
            print(f"{pad}  orelse:")
            for s in d['orelse']: dump(s, indent+2)
    elif isinstance(d, list):
        for s in d: dump(s, indent)
    else:
        print(f"{pad}{d!r}")
ast_dict = gen.generate()
print("TOP:", type(ast_dict))
if isinstance(ast_dict, list):
    for s in ast_dict: dump(s, 0)
else:
    dump(ast_dict, 0)
