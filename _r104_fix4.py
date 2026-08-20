import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = """                if not has_exc_instr and (succs_outside or is_terminal) and pred_in_try and not _is_simple_nontrivial_return:
                    self.generated_blocks.add(block)
                    continue"""

new_text = """                # [R08 fix] Do not skip continue-only blocks (NOP + JUMP_BACKWARD).
                # These are try-body continue statements, not finally normal-path copies.
                # A continue block has only JUMP_BACKWARD (and noise) instructions.
                _is_continue_block = False
                _blk_meaningful = [i for i in block.instructions
                                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if _blk_meaningful and all(i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                            for i in _blk_meaningful):
                    _is_continue_block = True
                if not _is_continue_block and not has_exc_instr and (succs_outside or is_terminal) and pred_in_try and not _is_simple_nontrivial_return:
                    self.generated_blocks.add(block)
                    continue"""

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("Old text NOT found!")
    # Find the exact location
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'not has_exc_instr and (succs_outside or is_terminal)' in line:
            for j in range(max(0, i-2), min(len(lines), i+5)):
                print(f"  {j+1}: {repr(lines[j])}")
            break
