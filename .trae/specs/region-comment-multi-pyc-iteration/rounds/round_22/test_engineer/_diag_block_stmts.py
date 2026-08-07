"""R22: trace _generate_block_statements for api_base while-else"""
import marshal, sys, types, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

with open(pyc_path, 'rb') as f:
    f.read(16)
    root = marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

for c in collect(root, []):
    if c.co_name == 'decorate_api_exc':
        code = c
        break

cfg = build_cfg(code)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Find the LoopRegion for decorate_api_exc
loop_region = None
for r in ra.regions:
    if isinstance(r, LoopRegion) and r.entry.start_offset == 0:
        loop_region = r
        break

print(f'LoopRegion else_blocks={[b.start_offset for b in loop_region.else_blocks]}')

# Generate AST
gen = RegionASTGenerator(cfg, ra)

# Trace _generate_block_statements for block@104 and block@106
blocks = sorted(
    (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)),
    key=lambda x: x.start_offset
)
b104 = [b for b in blocks if b.start_offset == 104][0]
b106 = [b for b in blocks if b.start_offset == 106][0]

# Generate statements for each block
stmts_104 = gen._generate_block_statements(b104)
stmts_106 = gen._generate_block_statements(b106)

print(f'block@104 statements: {stmts_104}')
print(f'block@106 statements: {stmts_106}')
