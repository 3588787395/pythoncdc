"""Temporary trace 2: trace reconstruct/_build_statement calls for block @8."""
import sys, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

PYC = r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc"
f = open(PYC, 'rb'); f.read(16)
module_code = marshal.load(f)
target = None
for const in module_code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'if_in_while':
        target = const
        break

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

cfg = build_cfg(target)
gen = RegionASTGenerator(cfg, top_level_code=None)

# patch after construction so instance attributes exist
orig_bs = gen._build_statement
def bs(instrs):
    r = orig_bs(instrs)
    offs = [getattr(i, 'offset', '?') for i in instrs]
    print(f"_build_statement(instrs@{offs}) = {repr(r)[:200]}")
    return r
gen._build_statement = bs

orig_recon = gen.expr_reconstructor.reconstruct
def recon(instrs, *a, **k):
    r = orig_recon(instrs, *a, **k)
    offs = [getattr(i, 'offset', '?') for i in instrs]
    if r is not None and any('Assign' in repr(r) for _ in [0]):
        print(f"reconstruct(instrs@{offs}) = {repr(r)[:200]}")
    elif r is not None and getattr(r, 'get', lambda x: None)('type') == 'Assign':
        print(f"reconstruct(instrs@{offs}) = ASSIGN {repr(r)[:200]}")
    return r
gen.expr_reconstructor.reconstruct = recon

ast_dict = gen.generate()
print("=== done ===")
