"""Apply fix6b - only apply fix6 in loop context to avoid regression."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                if _is_if_not:
                    _if_not_target = self.cfg.get_block_by_offset(_last_compare_last.argval)
                    if _if_not_target is not None:
                        else_succ = _if_not_target
                    else:"""

new_code = """                if _is_if_not:
                    _if_not_target = self.cfg.get_block_by_offset(_last_compare_last.argval)
                    # [spf-r01-fix6b] 仅在循环内（else: pass 编译为 JUMP_BACKWARD 回边）
                    # 才将 else_succ 改为 IF_TRUE 跳转目标。非循环内 `else: pass`
                    # 编译为 NOP，由 fix3 在 AST 生成时处理 merge_block NOP。
                    _in_loop_ctx = any(block in lr.blocks for lr in loop_regions)
                    if _if_not_target is not None and _in_loop_ctx:
                        else_succ = _if_not_target
                    else:"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix6b applied successfully!")
else:
    print("ERROR: old code not found for fix6b!")
