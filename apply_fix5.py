"""Apply fix5 - extend fix3 to also handle JUMP_BACKWARD merge_block in loops."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                # [spf-r01-fix3] 当 merge_block 仅含 NOP 时，源码有 `else: pass`
                # （CPython 3.11+ 为 else: pass 生成 NOP 占位指令）。丢弃 else 会导致
                # 重新编译时不生成 NOP，使 POP_JUMP_FORWARD_IF_TRUE 目标偏移 -2。
                # 典型：`if not a < b <= c: for... else: pass`
                _mb = getattr(region, 'merge_block', None)
                if _mb is not None:
                    _mb_meaningful = [i for i in _mb.instructions
                                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if not _mb_meaningful:
                        return [{'type': 'Pass'}]
                return None"""

new_code = """                # [spf-r01-fix3] 当 merge_block 仅含 NOP 时，源码有 `else: pass`
                # （CPython 3.11+ 为 else: pass 生成 NOP 占位指令）。丢弃 else 会导致
                # 重新编译时不生成 NOP，使 POP_JUMP_FORWARD_IF_TRUE 目标偏移 -2。
                # 典型：`if not a < b <= c: for... else: pass`（非循环内）
                # [spf-r01-fix5] 扩展：在循环内 `else: pass` 编译为 JUMP_BACKWARD
                # 回边（隐式 continue），不生成 NOP。merge_block 仅含 JUMP_BACKWARD
                # 时也需生成 else: pass，否则丢失回边指令导致 FOR_ITER 目标偏移 -2。
                # 典型：`for x: if not a < x <= b: for item: ... else: pass`（循环内）
                _mb = getattr(region, 'merge_block', None)
                if _mb is not None:
                    _mb_meaningful = [i for i in _mb.instructions
                                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                          'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
                    if not _mb_meaningful:
                        return [{'type': 'Pass'}]
                return None"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix5 applied successfully!")
else:
    print("ERROR: old code not found for fix5!")
