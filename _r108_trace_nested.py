"""Detailed trace of nested_try_regions detection."""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion
import core.cfg.region_ast_generator as rag

orig = rag.RegionASTGenerator._generate_try_body

def traced(self, region):
    if region.entry and region.entry.start_offset == 26:
        print(f"\n=== _generate_try_body(entry=26) ===")
        # Reproduce nested_try_regions detection
        for r in self.region_analyzer.regions:
            if isinstance(r, TryExceptRegion) and r is not region:
                is_child = r.parent is region
                is_in_try_blocks = r.entry in set(region.try_blocks)
                is_entry_in_handler = False
                for _, _, hblocks in region.except_handlers:
                    if r.entry in hblocks:
                        is_entry_in_handler = True
                        break
                if not is_entry_in_handler and getattr(region, 'finally_blocks', None):
                    if r.entry in set(region.finally_blocks):
                        is_entry_in_handler = True
                is_entry_in_else = bool(getattr(region, 'else_blocks', None) and r.entry in set(region.else_blocks))
                is_child_in_try = is_child and not is_entry_in_handler and not is_entry_in_else
                # Check _is_in_if_branch
                _is_in_if_branch = False
                for _ir in self.region_analyzer.regions:
                    if (isinstance(_ir, IfRegion) and _ir is not region
                            and getattr(_ir, 'parent', None) is region
                            and _ir.entry is not None):
                        _ir_then_set = set(_ir.then_blocks) if _ir.then_blocks else set()
                        _ir_else_set = set(_ir.else_blocks) if _ir.else_blocks else set()
                        if r.entry in _ir_then_set or r.entry in _ir_else_set:
                            _is_in_if_branch = True
                            break
                print(f"  Try@{r.entry.start_offset}: is_child={is_child}, is_in_try_blocks={is_in_try_blocks}, is_child_in_try={is_child_in_try}, _is_in_if_branch={_is_in_if_branch}")
                print(f"    parent is region: {r.parent is region}, r.parent={type(r.parent).__name__ if r.parent else 'None'}")
                if r.parent is region:
                    print(f"    region type={type(region).__name__}, region.entry={region.entry.start_offset}")
    result = orig(self, region)
    return result

rag.RegionASTGenerator._generate_try_body = traced

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

builder = CFGBuilder()
cfg = builder.build(ehc)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()
