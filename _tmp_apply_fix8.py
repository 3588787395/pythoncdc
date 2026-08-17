#!/usr/bin/env python3
"""Apply the for-else break target exclusion fix"""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            if _filtered_else_blocks:
                _added = set()
                for _eb in _filtered_else_blocks:
                    for _succ in _eb.successors:
                        if _succ in _added or _succ in _filtered_else_blocks:
                            continue
                        _succ_er = self.region_analyzer.get_entry_region_for_block(_succ)
                        if isinstance(_succ_er, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                            _srid = id(_succ_er)
                            if (_srid not in self._generated_regions
                                    and _srid not in self._generating_regions):
                                _added.add(_succ)
                if _added:
                    _filtered_else_blocks.extend(_added)
                    _filtered_else_blocks.sort(key=lambda b: b.start_offset)
            else_stmts = self._if_generate_branch_stmts(_filtered_else_blocks) if _filtered_else_blocks else []"""

new = """            if _filtered_else_blocks:
                # [Round 04 fix] break target exclusion
                _break_target_set = set()
                if region.break_blocks:
                    _body_set = set(region.body_blocks) | {region.header_block}
                    for _bb in region.break_blocks:
                        for _bsucc in _bb.successors:
                            if _bsucc not in _body_set:
                                _break_target_set.add(_bsucc)
                _added = set()
                for _eb in _filtered_else_blocks:
                    for _succ in _eb.successors:
                        if _succ in _added or _succ in _filtered_else_blocks:
                            continue
                        if _succ in _break_target_set:
                            continue
                        _succ_er = self.region_analyzer.get_entry_region_for_block(_succ)
                        if isinstance(_succ_er, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                            _srid = id(_succ_er)
                            if (_srid not in self._generated_regions
                                    and _srid not in self._generating_regions):
                                _added.add(_succ)
                if _added:
                    _filtered_else_blocks.extend(_added)
                    _filtered_else_blocks.sort(key=lambda b: b.start_offset)
            else_stmts = self._if_generate_branch_stmts(_filtered_else_blocks) if _filtered_else_blocks else []"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
    # Try to find a partial match
    if '_added = set()' in content:
        idx = content.find('_added = set()')
        print(f'Found _added = set() at index {idx}')
        print(f'Context: {content[idx-200:idx+200]!r}')
