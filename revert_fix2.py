"""Revert fix2 - it caused too many regressions."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the fix2 block
old_code = """                        # [spf-r01-fix2] 对称检测：当 else_succ 是 continue sink
                        # （JUMP_BACKWARD 到循环头）时，else 分支退出当前循环迭代、
                        # 永不与 then 分支在循环内汇聚，故 then_succ 是顺序 fall-through
                        # （if 之后的下一条循环体语句），merge 应为 then_succ。
                        # 典型场景：`if not a < x <= b: for item in ...: ... else: pass`
                        # POP_JUMP_IF_TRUE 跳到 else_succ=JUMP_BACKWARD（else: pass =
                        # continue 语义），then_succ 是 for 循环入口。
                        # 不设 merge=then_succ 会使 NCPD 返回循环头，导致 then_blocks
                        # 过度收集或 else_blocks 误包含循环回边块，产生 `pass` 代替
                        # 真实 then 体。
                        _else_last = else_succ.get_last_instruction()
                        if (_else_last is not None
                                and _else_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                and _else_last.argval == _header.start_offset):
                            _then_last = then_succ.get_last_instruction()
                            _elif2 = (
                                len(then_succ.conditional_successors) == 2
                                and _then_last is not None
                                and _then_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)
                            )
                            if not _elif2:
                                merge = then_succ"""

if old_code in content:
    content = content.replace(old_code, '', 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix2 reverted successfully!")
else:
    print("ERROR: fix2 code not found!")
