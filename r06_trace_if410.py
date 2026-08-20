#!/usr/bin/env python3
"""Patch trace: Add debug logging to trace how block @410 is handled"""

import sys, types
sys.path.insert(0, '.')

# Monkey-patch to add tracing
import core.cfg.region_ast_generator as rag

# Save original methods
_orig_dispatch = rag.RegionASTGenerator._loop_dispatch_block
_orig_generate_block = rag.RegionASTGenerator._generate_block_statements
_orig_loop_handle_exit = None
_orig_loop_handle_no_exit = None

# Find the methods
for name in dir(rag.RegionASTGenerator):
    if 'exit_successors' in name:
        _orig_loop_handle_exit = getattr(rag.RegionASTGenerator, name)
        rag.RegionASTGenerator._traced_exit = _orig_loop_handle_exit
    if 'no_exit' in name and 'successor' in name:
        _orig_loop_handle_no_exit = getattr(rag.RegionASTGenerator, name)
        rag.RegionASTGenerator._traced_no_exit = _orig_loop_handle_no_exit

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import BlockRole
import marshal

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all(code, prefix=""):
    name = prefix + code.co_name if prefix else code.co_name
    result = {name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            new_prefix = name + "." if name != "<module>" else ""
            result.update(extract_all(const, new_prefix))
    return result

orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
orig_codes = extract_all(orig_code)

target = "DataProcessor.validate_data"
orig_co = orig_codes[target]

cfg = CFGBuilder().build(orig_co)

# Monkey-patch _loop_dispatch_block to trace block @410
def traced_dispatch(self, block, region, child_info, boolop_for_while,
                     body_stmts, body_blocks_no_header, back_edge_stmts,
                     natural_back_edge, back_edge_source_blocks):
    if block.start_offset == 410:
        print(f"\n=== DISPATCH Block @410 ===")
        print(f"  Role: {self.region_analyzer.get_block_role(block)}")
        print(f"  Successors: {[s.start_offset for s in block.successors]}")
        for s in block.successors:
            sr = self.region_analyzer.get_block_role(s)
            print(f"    Succ @{s.start_offset}: role={sr}")
        # Check exit successors
        _exit_succs = child_info.get('exit_succs', [])
        print(f"  exit_succs in child_info: {[s.start_offset for s in _exit_succs]}")

    result = _orig_dispatch(self, block, region, child_info, boolop_for_while,
                            body_stmts, body_blocks_no_header, back_edge_stmts,
                            natural_back_edge, back_edge_source_blocks)

    if block.start_offset == 410:
        print(f"  After dispatch: handled={result}")
        print(f"  body_stmts so far: {[s.get('type','?') if isinstance(s,dict) else type(s).__name__ for s in body_stmts]}")
        print(f"  body_blocks_no_header: {[b.start_offset for b in body_blocks_no_header]}")
        print(f"  Generated: {448 in self.generated_offsets}, {488 in self.generated_offsets}")

    return result

rag.RegionASTGenerator._loop_dispatch_block = traced_dispatch

# Also trace _loop_handle_exit_successors
_orig_exit = rag.RegionASTGenerator._loop_handle_exit_successors
def traced_exit(self, block, region, child_info, boolop_for_while,
                body_stmts, body_blocks_no_header, back_edge_stmts,
                natural_back_edge, back_edge_source_blocks):
    if block.start_offset == 410:
        print(f"\n=== EXIT_SUCC Block @410 ===")

    _orig_exit(self, block, region, child_info, boolop_for_while,
               body_stmts, body_blocks_no_header, back_edge_stmts,
               natural_back_edge, back_edge_source_blocks)

    if block.start_offset == 410:
        print(f"  After exit_succs: body_stmts={[s.get('type','?') if isinstance(s,dict) else type(s).__name__ for s in body_stmts]}")
        print(f"  body_blocks_no_header: {[b.start_offset for b in body_blocks_no_header]}")
        print(f"  Generated: 448={448 in self.generated_offsets}, 488={488 in self.generated_offsets}")

rag.RegionASTGenerator._loop_handle_exit_successors = traced_exit

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final result: {len(result) if result else 0} nodes ===")
print(f"Generated offsets: {sorted(gen.generated_offsets)}")
print(f"448 generated: {448 in gen.generated_offsets}")
print(f"488 generated: {488 in gen.generated_offsets}")