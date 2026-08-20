#!/usr/bin/env python3
"""Patch _process_if_blocks to add debug prints around the LOOP_BODY structural region detection"""

import shutil

src_path = 'core/cfg/region_ast_generator.py'
dst_path = 'core/cfg/region_ast_generator_debug2.py'

with open(src_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the LOOP_BODY structural region detection and add debug prints
old_code = """            if role == BlockRole.LOOP_BODY and self._current_loop:
                _nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if isinstance(_nested_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                    _nrid = id(_nested_region)
                    if _nrid not in self._generated_regions and _nrid not in self._generating_regions:
                        _nr_ast = self._generate_region(_nested_region)"""

new_code = """            if role == BlockRole.LOOP_BODY and self._current_loop:
                _nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if block.start_offset in (410, 448, 488):
                    import sys as _dbg_sys2
                    print(f"DBG @{block.start_offset}: nested_region={type(_nested_region).__name__ if _nested_region else None} entry={_nested_region.entry.start_offset if _nested_region and hasattr(_nested_region,'entry') and _nested_region.entry else None}", file=_dbg_sys2.stderr)
                if isinstance(_nested_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                    _nrid = id(_nested_region)
                    if block.start_offset in (410, 448, 488):
                        import sys as _dbg_sys3
                        print(f"DBG @{block.start_offset}: _nrid={_nrid} in_generated={_nrid in self._generated_regions} in_generating={_nrid in self._generating_regions}", file=_dbg_sys3.stderr)
                    if _nrid not in self._generated_regions and _nrid not in self._generating_regions:
                        _nr_ast = self._generate_region(_nested_region)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    # Also patch the 14980 line (general structural region detection)
    old2 = """            _region = self.region_analyzer.get_entry_region_for_block(block)
            if isinstance(_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                _rid = id(_region)
                if (_rid not in self._generated_regions
                        and _rid not in self._generating_regions):
                    self._generating_regions.add(_rid)
                    try:
                        _ast = self._generate_region(_region)"""
    new2 = """            _region = self.region_analyzer.get_entry_region_for_block(block)
            if block.start_offset in (410, 448, 488):
                import sys as _dbg_sys4
                print(f"DBG2 @{block.start_offset}: _region={type(_region).__name__ if _region else None} entry={_region.entry.start_offset if _region and hasattr(_region,'entry') and _region.entry else None}", file=_dbg_sys4.stderr)
            if isinstance(_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                _rid = id(_region)
                if block.start_offset in (410, 448, 488):
                    import sys as _dbg_sys5
                    print(f"DBG2 @{block.start_offset}: _rid={_rid} in_generated={_rid in self._generated_regions} in_generating={_rid in self._generating_regions}", file=_dbg_sys5.stderr)
                if (_rid not in self._generated_regions
                        and _rid not in self._generating_regions):
                    self._generating_regions.add(_rid)
                    try:
                        _ast = self._generate_region(_region)"""
    if old2 in content:
        content = content.replace(old2, new2, 1)

    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Debug version written to {dst_path}")
else:
    print("Target not found!")