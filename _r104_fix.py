import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact old text
old_text = """        if not nested_elif_stmts and region.elif_final_else:
            _efe_is_continue_only_2 = all(
                (self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)
                 and not [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')])
                for b in region.elif_final_else
            )
            if not _efe_is_continue_only_2:
                final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')"""

# Check if old text exists
if old_text in content:
    print("Found old text at position:", content.index(old_text))
    
    new_text = """        if not nested_elif_stmts and region.elif_final_else:
            # [R04 fix] Mirror first check (line 11885-11888): use instruction-based
            # detection instead of block role. A LOOP_BACK_EDGE block can also be a
            # continue statement. When elif_final_else blocks contain only
            # JUMP_BACKWARD, identify as else: continue.
            _efe_is_continue_only_2 = all(
                (not [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')])
                and any(i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') for i in b.instructions)
                for b in region.elif_final_else
            )
            if _efe_is_continue_only_2:
                for _fe_b in region.elif_final_else:
                    self.generated_blocks.add(_fe_b)
                final_else_stmts = [{'type': 'Continue'}]
            else:
                final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')"""
    
    content = content.replace(old_text, new_text, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replacement successful!")
else:
    print("Old text NOT found!")
    # Try to find a close match
    import difflib
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '_efe_is_continue_only_2' in line and 'get_block_role' in line:
            print(f"Line {i+1}: {repr(line)}")
        if '_efe_is_continue_only_2' in line and 'PURE_CONTINUE' in line:
            print(f"Line {i+1}: {repr(line)}")
    # Print context around line 11908
    for i in range(11906, 11923):
        if i < len(lines):
            print(f"  {i+1}: {repr(lines[i])}")
