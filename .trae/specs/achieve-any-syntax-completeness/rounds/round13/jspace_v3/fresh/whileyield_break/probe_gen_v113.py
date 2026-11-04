# rr-v5r113 生成层状态追踪：每个 gen 实例的 regions / generated_blocks /
# top_level 是否被「全块已生成」跳过 / 降级调用。
import sys, os, marshal
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import region_analyzer as RA

REPRO = 'D:/temp/opencode/cl_layout/r112diag_a/repro'
OUT = 'D:/temp/opencode/cl_layout/r113diag'
CASES = ['r1_while_yield_break', 'r3_while_yield_no_break', 'r4_exact_shape']


def off(b):
    return b.start_offset if b is not None else None


def so(bs):
    return ', '.join(str(x.start_offset) for x in sorted(bs, key=lambda z: z.start_offset)) if bs else ''


_orig_generate = RegionASTGenerator.generate
_orig_gen_region = RegionASTGenerator._generate_region
_orig_gen_loop = RegionASTGenerator._generate_loop
_orig_degraded = getattr(RegionASTGenerator, '_generate_degraded_statements', None)
ALL_GENS = []
CALL_LOG = []


def w_generate(self):
    if self not in ALL_GENS:
        ALL_GENS.append(self)
    CALL_LOG.append(('generate', id(self), self.cfg.name))
    return _orig_generate(self)


def w_gen_region(self, region, *a, **kw):
    CALL_LOG.append(('_generate_region', id(self), type(region).__name__, off(getattr(region, 'entry', None))))
    return _orig_gen_region(self, region, *a, **kw)


def w_gen_loop(self, region, *a, **kw):
    CALL_LOG.append(('_generate_loop', id(self), type(region).__name__, off(getattr(region, 'entry', None))))
    return _orig_gen_loop(self, region, *a, **kw)


RegionASTGenerator.generate = w_generate
RegionASTGenerator._generate_region = w_gen_region
RegionASTGenerator._generate_loop = w_gen_loop
if _orig_degraded is not None:
    def w_degraded(self, *a, **kw):
        CALL_LOG.append(('_generate_degraded_statements', id(self), '', ''))
        return _orig_degraded(self, *a, **kw)
    RegionASTGenerator._generate_degraded_statements = w_degraded

os.makedirs(OUT, exist_ok=True)
for name in CASES:
    ALL_GENS.clear()
    CALL_LOG.clear()
    pyc = REPRO + '/%s_orig.pyc' % name
    code = marshal.loads(open(pyc, 'rb').read()[16:])
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    out = ['==== %s ====' % name]
    try:
        gen.generate()
    except Exception as e:
        import traceback
        out.append('EXCEPTION %r' % e)
        out += traceback.format_exc().splitlines()
    for g in ALL_GENS:
        out.append('--- GEN cfg=%s id=%s ---' % (g.cfg.name, id(g)))
        regs = getattr(g, 'regions', None) or []
        for r in regs:
            rbs = getattr(r, 'blocks', None) or set()
            allgen = all(b in g.generated_blocks for b in rbs) if rbs else False
            out.append('  %-14s entry=@%-5s parent=%s blocks=[%s] ALL-GENERATED=%s' % (
                type(r).__name__, off(getattr(r, 'entry', None)),
                'Y' if getattr(r, 'parent', None) is not None else 'N',
                so(rbs), allgen))
        out.append('  generated_blocks=[%s]' % so(g.generated_blocks))
    out.append('--- CALL LOG ---')
    for c in CALL_LOG:
        if c[0] == 'generate':
            out.append('  generate            id=%s cfg=%s' % (c[1], c[2]))
        else:
            out.append('  %-32s id=%s %s @%s' % (c[0], c[1], c[2], c[3] if len(c) > 3 else ''))
    open(OUT + '/gen_%s.txt' % name, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(name, '->', len(out), 'lines, gens=', len(ALL_GENS))
