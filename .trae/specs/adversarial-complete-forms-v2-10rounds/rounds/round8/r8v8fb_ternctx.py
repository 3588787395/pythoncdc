import marshal
import sys
import types

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TernaryRegion


def find_code(code, name):
    found = []

    def walk(c):
        for const in c.co_consts:
            if isinstance(const, types.CodeType):
                if const.co_name == name:
                    found.append(const)
                walk(const)
    walk(code)
    return found


pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = find_code(code, name)
co = targets[0]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
an = gen.region_analyzer
an.analyze()
import io
out = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for r in an.regions:
    if isinstance(r, TernaryRegion):
        out.write('TERNARY entry=@%s merge=@%s merge_context=%r value_target=%r cond_chain=%s true=@%s false=@%s\n' % (
            getattr(r.entry, 'start_offset', None),
            getattr(r.merge_block, 'start_offset', None),
            getattr(r, 'merge_context', None),
            getattr(r, 'value_target', None),
            [(getattr(b, 'start_offset', b), o) for b, o in (getattr(r, 'condition_chain_blocks', None) or [])],
            getattr(getattr(r, 'true_value_block', None), 'start_offset', None),
            getattr(getattr(r, 'false_value_block', None), 'start_offset', None)))
out.flush()
