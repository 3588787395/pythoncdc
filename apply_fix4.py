"""Apply fix4 - precise else_succ continue sink detection for if-not-chained-compare pattern."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = "                            if not _elif:\n                                merge = else_succ\n\n\n            if merge is None:"

new_code = """                            if not _elif:
                                merge = else_succ
                        # [spf-r01-fix4] 对称检测：当 else_succ 是 continue sink
                        # 且 then_succ 以 JUMP_FORWARD 结尾（if-not 链式比较模式）时，
                        # else 分支是 else: pass（在循环内编译为 JUMP_BACKWARD 回边），
                        # then 分支包含实际代码（for 循环等）。设 merge=else_succ 使
                        # then_blocks 包含完整 then 分支（含 for 循环），else_blocks 为空。
                        # AST 生成时 _is_chained_compare_cleanup_else 检测 merge_block 为
                        # continue sink（JUMP_BACKWARD）→ 生成 else: pass。
                        # 精确条件（避免回归）：
                        #   1. else_succ 是 JUMP_BACKWARD 到循环头（continue sink）
                        #   2. then_succ 以 JUMP_FORWARD 结尾（非 JUMP_BACKWARD = 非 continue）
                        #   3. then_succ 的 JUMP_FORWARD 目标不等于当前 merge（有实际 then 体）
                        _else_last2 = else_succ.get_last_instruction()
                        if (_else_last2 is not None
                                and _else_last2.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                and _else_last2.argval == _header.start_offset):
                            _then_last2 = then_succ.get_last_instruction()
                            if (_then_last2 is not None
                                    and _then_last2.opname == 'JUMP_FORWARD'
                                    and _then_last2.argval is not None):
                                _jf_target = self.cfg.get_block_by_offset(_then_last2.argval)
                                if _jf_target is not None and _jf_target != merge:
                                    merge = else_succ


            if merge is None:"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix4 applied successfully!")
else:
    print("ERROR: old code not found for fix4!")
    # Debug
    idx = content.find("merge = else_succ\n\n\n            if merge is None:")
    if idx >= 0:
        print(f"Found at position {idx}")
    else:
        idx = content.find("merge = else_succ")
        if idx >= 0:
            print(f"Found 'merge = else_succ' at position {idx}")
            print(f"Context: {repr(content[idx:idx+100])}")
