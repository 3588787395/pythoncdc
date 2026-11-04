# rr-v5r113 捕获 _generate_loop 在「尾部 break」形态下抛出的确切异常与行号。
import sys, os, marshal, traceback
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

REPRO = 'D:/temp/opencode/cl_layout/r112diag_a/repro'
OUT = 'D:/temp/opencode/cl_layout/r113diag'
CASES = ['r1_while_yield_break', 'r2_while_yield_preinit',
         'r3_while_yield_no_break', 'r4_exact_shape']

_orig = RegionASTGenerator._generate_loop
EXC = []


def w(self, region, *a, **kw):
    try:
        return _orig(self, region, *a, **kw)
    except Exception as e:
        EXC.append((self.cfg.name, region.entry.start_offset if region.entry else None,
                    repr(e), traceback.format_exc()))
        raise


RegionASTGenerator._generate_loop = w

os.makedirs(OUT, exist_ok=True)
lines = []
for name in CASES:
    EXC.clear()
    pyc = REPRO + '/%s_orig.pyc' % name
    code = marshal.loads(open(pyc, 'rb').read()[16:])
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    try:
        gen.generate()
    except Exception as e:
        lines.append('%s OUTER EXC %r' % (name, e))
    lines.append('==== %s : _generate_loop exceptions = %d ====' % (name, len(EXC)))
    for fn, ent, rep, tb in EXC:
        lines.append('  cfg=%s entry=@%s exc=%s' % (fn, ent, rep))
        lines.append('  ---- traceback (last 30 lines) ----')
        for l in tb.strip().splitlines()[-30:]:
            lines.append('    ' + l)
open(OUT + '/exc.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('written', len(lines), 'lines')
for n, e, rep, tb in EXC:
    print(n, rep)
