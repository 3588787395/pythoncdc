"""Debug script for adv02_ternary_second_or to trace op_chain construction"""
import sys
import dis
sys.path.insert(0, '/workspace')

# Monkey-patch _detect_boolop_conditional_chain to print debug info
from core.cfg import region_analyzer as ra_mod
original_detect = ra_mod.RegionAnalyzer._detect_boolop_conditional_chain

def traced_detect(self, start_block, claimed, skip_claimed_check=False):
    chain = original_detect(self, start_block, claimed, skip_claimed_check)
    if chain is not None:
        print(f"  _detect_boolop_conditional_chain(start={start_block.start_offset}) → {[(b.start_offset, op) for b, op in chain]}")
    return chain

ra_mod.RegionAnalyzer._detect_boolop_conditional_chain = traced_detect

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator


SOURCE = """if a or (b if c else d):
    pass"""

code = compile(SOURCE, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== Final regions ===")
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        print(f"  BoolOpRegion: op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
        for cb, op in r.op_chain:
            last = cb.get_last_instruction()
            print(f"    block {cb.start_offset}: last={last.opname} argval={last.argval}, op={op}")
