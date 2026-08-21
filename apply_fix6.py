"""Apply fix6 - correct else_succ for if-not chained compare pattern."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                # 调整 else_succ：跳过清理块（POP_TOP + JUMP），直接指向清理块的后继
                _else_instrs = [i for i in else_succ.instructions
                                if i.opname not in NOISE_OPS
                                and i.opname not in ('RESUME', 'NOP', 'CACHE')]
                _else_is_cleanup = all(
                    i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    for i in _else_instrs
                ) and len(else_succ.successors) == 1
                if _else_is_cleanup:
                    else_succ = list(else_succ.successors)[0]"""

new_code = """                # 调整 else_succ：跳过清理块（POP_TOP + JUMP），直接指向清理块的后继
                # [spf-r01-fix6] 当链式比较末尾使用 POP_JUMP_FORWARD_IF_TRUE
                # （if-not 模式，如 `if not a < b <= c:`）时，最后一个比较块的
                # 跳转目标才是真正的 else 分支入口。清理块的后继属于 then 分支。
                # 例如：block 56 POP_JUMP_IF_TRUE → 124 (else: pass / continue sink)
                #       block 68 POP_TOP → 70 (then 分支的 LOAD_CONST)
                # 原 else_succ=68 → 跳过后继=70（错误，70 是 then 分支）
                # 修正：else_succ = 链式比较末尾 POP_JUMP_IF_TRUE 的跳转目标=124
                _last_compare_last = last_compare.get_last_instruction()
                _is_if_not = (_last_compare_last is not None
                              and _last_compare_last.opname in ('POP_JUMP_FORWARD_IF_TRUE',
                                                                'POP_JUMP_IF_TRUE',
                                                                'POP_JUMP_BACKWARD_IF_TRUE')
                              and _last_compare_last.argval is not None)
                if _is_if_not:
                    _if_not_target = self.cfg.get_block_by_offset(_last_compare_last.argval)
                    if _if_not_target is not None:
                        else_succ = _if_not_target
                    else:
                        _else_instrs = [i for i in else_succ.instructions
                                        if i.opname not in NOISE_OPS
                                        and i.opname not in ('RESUME', 'NOP', 'CACHE')]
                        _else_is_cleanup = all(
                            i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                            for i in _else_instrs
                        ) and len(else_succ.successors) == 1
                        if _else_is_cleanup:
                            else_succ = list(else_succ.successors)[0]
                else:
                    _else_instrs = [i for i in else_succ.instructions
                                    if i.opname not in NOISE_OPS
                                    and i.opname not in ('RESUME', 'NOP', 'CACHE')]
                    _else_is_cleanup = all(
                        i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                        for i in _else_instrs
                    ) and len(else_succ.successors) == 1
                    if _else_is_cleanup:
                        else_succ = list(else_succ.successors)[0]"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix6 applied successfully!")
else:
    print("ERROR: old code not found for fix6!")
