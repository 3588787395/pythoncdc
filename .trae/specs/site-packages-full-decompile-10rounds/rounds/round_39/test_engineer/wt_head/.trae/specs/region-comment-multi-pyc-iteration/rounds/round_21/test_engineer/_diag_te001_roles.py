"""R21 diag: check block roles for te001."""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

PYC = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/minimal_repros/__pycache__/te001_loop_continue.cpython-311.pyc'

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

for b in sorted((list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)), key=lambda x: x.start_offset):
    role = ra.get_block_role(b)
    print(f'block@{b.start_offset:4d} role={role}')
