"""Apply fix3 - don't discard else: pass when merge_block is NOP."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """        if region.chained_compare_blocks and region.else_blocks:
            if self._is_chained_compare_cleanup_else(region):
                return None"""

new_code = """        if region.chained_compare_blocks and region.else_blocks:
            if self._is_chained_compare_cleanup_else(region):
                # [spf-r01-fix3] 当 merge_block 仅含 NOP 时，源码有 `else: pass`
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

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix3 applied successfully!")
else:
    print("ERROR: old code not found for fix3!")
