"""R21 diag: te003 roles"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

PYC = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/minimal_repros/__pycache__/te003_loop_return.cpython-311.pyc'

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

code = load_pyc(PYC)
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'f':
        func_code = c
        break

cfg = build_cfg(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for b in sorted(blocks, key=lambda x: x.start_offset):
    role = ra.get_block_role(b)
    ops = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions
                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
    print(f'block@{b.start_offset:4d} role={role}: {ops}')

print()
for r in ra.regions:
    if type(r).__name__ == 'TryExceptRegion':
        print(f'TryExceptRegion entry@{r.entry.start_offset}')
        print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
        print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
        for exc, name, hb in r.except_handlers:
            for b in hb:
                role = ra.get_block_role(b)
                print(f'  handler block@{b.start_offset} role={role}')
