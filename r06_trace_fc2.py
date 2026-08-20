#!/usr/bin/env python3
"""Patch _process_if_blocks to trace block@410 path through LOOP_BODY detection"""

import sys, types
sys.path.insert(0, '.')

# Read source
with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    source = f.read()

# Find the LOOP_BODY check and add debug print
old = """            if role == BlockRole.LOOP_BODY and self._current_loop:
                _nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if isinstance(_nested_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):"""

new = """            if role == BlockRole.LOOP_BODY and self._current_loop:
                _nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if block.start_offset in (410, 448, 488):
                    import sys as _dbg_lb
                    print(f"LB @{block.start_offset}: _nested_region={type(_nested_region).__name__ if _nested_region else None} is_structural={isinstance(_nested_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES) if _nested_region else False}", file=_dbg_lb.stderr)
                if isinstance(_nested_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):"""

if old in source:
    source = source.replace(old, new, 1)

    # Also add debug right before _try_generate_conditional_break
    old2 = """                cond_break = self._try_generate_conditional_break(block)
                if cond_break is not None:"""
    new2 = """                if block.start_offset in (410, 448, 488):
                    import sys as _dbg_cb
                    print(f"CB @{block.start_offset}: about to try cond_break", file=_dbg_cb.stderr)
                cond_break = self._try_generate_conditional_break(block)
                if cond_break is not None:"""
    if old2 in source:
        source = source.replace(old2, new2, 1)

    # Also add debug for _nested_if_entry_generate check
    old3 = """            if block in _nested_if_entry_generate:
                _nr = _nested_if_entry_generate[block]"""
    new3 = """            if block.start_offset in (410, 448, 488):
                import sys as _dbg_nieg
                print(f"NIEG @{block.start_offset}: in_entry_gen={block in _nested_if_entry_generate}", file=_dbg_nieg.stderr)
            if block in _nested_if_entry_generate:
                _nr = _nested_if_entry_generate[block]"""
    if old3 in source:
        source = source.replace(old3, new3, 1)

    with open('core/cfg/region_ast_generator_debug3.py', 'w', encoding='utf-8') as f:
        f.write(source)
    print("Debug3 written!")
else:
    print("Target not found!")