import sys, marshal, types, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

os.environ['DBG_BOOLOP'] = '1'

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

exrights_code = code.co_consts[32]
cfg = build_cfg(exrights_code)
gen = RegionASTGenerator(cfg, top_level_code=exrights_code)
ast_dict = gen.generate()

analyzer = gen.region_analyzer
for r in gen.regions:
    if isinstance(r, BoolOpRegion):
        chain_info = [(b.start_offset, op) for b, op in r.op_chain]
        print("BoolOpRegion@{}: op_chain={}".format(r.entry.start_offset, chain_info))
