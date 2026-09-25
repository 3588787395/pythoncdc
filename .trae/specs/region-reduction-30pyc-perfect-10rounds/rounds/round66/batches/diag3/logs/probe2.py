import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg import build_cfg
from core.cfg import region_analyzer as RA
from core.cfg.region_analyzer import NOISE_OPS

d = io.open(sys.argv[1], 'rb').read()
top = marshal.loads(d[16:])
def walk(c, o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType): walk(k, o)
    return o
code = [c for c in walk(top, []) if c.co_name == sys.argv[2]][0]
cfg = build_cfg(code)
BL = cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks
print('NOISE_OPS =', sorted(NOISE_OPS))
for off in [int(x) for x in sys.argv[3].split(',')]:
    b = [x for x in BL if x.start_offset == off][0]
    eff = [i for i in b.instructions if i.opname not in NOISE_OPS]
    print('BLK@%d raw=%s' % (off, [(i.opname, i.argval) for i in b.instructions]))
    print('   eff=%s' % [(i.opname, i.argval) for i in eff])
    an = RA.RegionAnalyzer(cfg)
    print('   _is_single_expression_block =', an._is_single_expression_block(b))
    print('   _is_pure_expression_block   =', getattr(an, '_is_pure_expression_block', lambda x: 'NA')(b))
