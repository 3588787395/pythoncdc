import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg import build_cfg
from core.cfg import region_analyzer as RA
from core.cfg.region_ast_generator import RegionASTGenerator

d = io.open(sys.argv[1], 'rb').read()
top = marshal.loads(d[16:])
def walk(c, o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType): walk(k, o)
    return o
name = sys.argv[2]
code = [c for c in walk(top, []) if c.co_name == name][0]
cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=None)
an = gen.region_analyzer
regions = an.analyze()
BLK = cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks
print('SHORT_CIRCUIT_JUMP_OPS =', sorted(RA.SHORT_CIRCUIT_JUMP_OPS))
print('FORWARD_CONDITIONAL_JUMP_OPS =', sorted(RA.FORWARD_CONDITIONAL_JUMP_OPS))
b0 = [x for x in BLK if x.start_offset == 0][0]
print('blk@0 last =', b0.get_last_instruction().opname)
print('in block_to_region:', b0 in an.block_to_region,
      '->', type(an.block_to_region.get(b0)).__name__,
      'entry_is_blk:', an.block_to_region.get(b0) is not None and an.block_to_region[b0].entry is b0)
r = an.block_to_region.get(b0)
if r is not None:
    print('existing.can_be_ternary_header =', r.can_be_ternary_header(b0, an))
print('an._can_be_ternary_header(blk@0) =', an._can_be_ternary_header(b0))
# also check the chain-compare detection on b0
print('_is_chained_compare_header(b0) =', an._is_chained_compare_header(b0))
info = an._detect_chained_compare_pattern(b0)
print('_detect_chained_compare_pattern(b0) =', None if info is None else {k: ([(i.opname,i.argval) for i in v] if isinstance(v,list) and v and hasattr(v[0],'opname') else v) for k,v in info.items()})
