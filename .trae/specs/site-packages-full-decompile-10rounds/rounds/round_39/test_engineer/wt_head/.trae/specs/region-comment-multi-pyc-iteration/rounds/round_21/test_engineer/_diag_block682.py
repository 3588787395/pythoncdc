"""R21 diag: handlers.pyc _target block@682"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
targets = [c for c in collect(root, []) if c.co_name == '_target']
t = targets[-1]
cfg = build_cfg(t)
ra = RegionAnalyzer(cfg)
ra.analyze()

b682 = cfg.get_block_by_offset(682)
print(f'block@682 instructions:')
for i in b682.instructions:
    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG'):
        print(f'  {i.offset}: {i.opname} {getattr(i, "argval", "")}')

role = ra.get_block_role(b682)
print(f'\nrole={role}')

# Check what _generate_block_statements produces for this block
gen = RegionASTGenerator(cfg, ra)
stmts = gen._generate_block_statements(b682)
print(f'\n_generate_block_statements result:')
for s in stmts:
    print(f'  {s}')

# Check else_blocks
for r in ra.regions:
    if isinstance(r, TryExceptRegion) and r.entry.start_offset == 254:
        print(f'\nTryExceptRegion else_blocks:')
        for eb in r.else_blocks:
            ebr = ra.get_block_role(eb)
            print(f'  block@{eb.start_offset} role={ebr}')
