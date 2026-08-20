#!/usr/bin/env python3
"""Round 6 fix: Prevent _try_generate_conditional_break_or_continue from
recursively processing blocks that are entry points of structural regions
(IfRegion, LoopRegion, TryExceptRegion, etc.).

Root cause: When processing block@366 (BREAK role), the function recursively
calls itself on block@410 (the else branch), which is the entry of
IfRegion(IF_THEN, entry=410). The recursive call marks block@410 as generated
and produces `if len(item) > 50: break` instead of correctly generating the
IfRegion with its then_blocks (print + continue) and merge_block (print + continue).

Fix: Before the recursive call at line 16162, check if _bn_else_block is the
entry of any structural region. If so, skip the recursive call and let
_process_if_blocks handle it through the _nested_if_entry_generate path.
"""

import shutil

file_path = "core/cfg/region_ast_generator.py"
shutil.copy2(file_path, file_path + ".r06_backup")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: In _try_generate_conditional_break_or_continue, before the recursive
# call at line 16162, check if _bn_else_block is a structural region entry
old_code = """                elif _bn_else_block not in self.generated_blocks:
                    _bn_else_last = _bn_else_block.get_last_instruction()
                    _bn_else_cb_result = None
                    if (_bn_else_last is not None
                        and _bn_else_last.opname in FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS
                        and self._current_loop is not None):
                        _bn_else_cb_result = self._try_generate_conditional_break_or_continue(_bn_else_block)"""

new_code = """                elif _bn_else_block not in self.generated_blocks:
                    _bn_else_last = _bn_else_block.get_last_instruction()
                    _bn_else_cb_result = None
                    if (_bn_else_last is not None
                        and _bn_else_last.opname in FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS
                        and self._current_loop is not None):
                        # [Round 6 fix] Don't recursively process blocks that are
                        # entry points of structural regions (IfRegion, LoopRegion,
                        # TryExceptRegion, etc.). The recursive call would mark the
                        # block as generated and produce incorrect break/continue
                        # code, losing the region's internal structure (then_blocks,
                        # else_blocks, merge_block). Let _process_if_blocks handle
                        # these blocks through the _nested_if_entry_generate path.
                        _bn_else_is_region_entry = False
                        _bn_else_er = self.region_analyzer.get_entry_region_for_block(_bn_else_block)
                        if _bn_else_er is not None and isinstance(_bn_else_er, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
                            _bn_else_is_region_entry = True
                        if not _bn_else_is_region_entry:
                            _bn_else_cb_result = self._try_generate_conditional_break_or_continue(_bn_else_block)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    print("Fix 1 applied: prevent recursive cond_break on structural region entries")
else:
    print("ERROR: Fix 1 target not found!")

# Fix 2: Also fix the _try_generate_conditional_break function to check
# if the block being processed is a structural region entry
old_code2 = """    def _try_generate_conditional_break(self, block: BasicBlock) -> Optional[List[Dict[str, Any]]]:
        \"\"\"\"\"\"
        if not self._current_loop:
            return None
        result = self._try_generate_conditional_break_or_continue(block)"""

new_code2 = """    def _try_generate_conditional_break(self, block: BasicBlock) -> Optional[List[Dict[str, Any]]]:
        \"\"\"\"\"\"
        if not self._current_loop:
            return None
        # [Round 6 fix] Don't process blocks that are entry points of structural
        # regions. These blocks should be handled by _process_if_blocks through
        # the _nested_if_entry_generate path, which correctly generates the
        # region's internal structure.
        _block_er = self.region_analyzer.get_entry_region_for_block(block)
        if _block_er is not None and isinstance(_block_er, RegionASTGenerator._STRUCTURAL_REGION_TYPES):
            _er_id = id(_block_er)
            if _er_id not in self._generated_regions and _er_id not in self._generating_regions:
                return None
        result = self._try_generate_conditional_break_or_continue(block)"""

if old_code2 in content:
    content = content.replace(old_code2, new_code2, 1)
    print("Fix 2 applied: prevent cond_break on structural region entries in _try_generate_conditional_break")
else:
    print("ERROR: Fix 2 target not found!")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("All fixes applied!")