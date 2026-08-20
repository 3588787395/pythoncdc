"""Apply dtc-r08 fix: replace _region_block_set with _known_struct in finally_copy_blocks post-try detection"""
import re

path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):
                _region_block_set = set(region.blocks)
                for _fc_offset, _fc_keep in region.finally_copy_blocks.items():
                    _fc_block = self.cfg.get_block_by_offset(_fc_offset)
                    if _fc_block is None:
                        continue
                    for _succ in _fc_block.successors:
                        if (_succ not in _region_block_set
                                and _succ not in _post_try_seen_r19n2
                                and _succ not in _handler_entry_blocks):"""

new = """            # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
            # 当 has_finally=True 且 else 分支含 return 时，CPython 编译器将
            # finally 正常路径副本的 JUMP_FORWARD 目标设为 try-except-else-finally
            # 之后的代码（如 `return None`）。该目标块在区域识别阶段被纳入
            # TryExceptRegion.blocks（因其在 try_offset 范围内），但不属于
            # try_blocks / else_blocks / finally_blocks / handler_blocks /
            # finally_copy_keys 中的任何部分。依「每块唯一归属」：该块的结构
            # 归属是 post-try 顺序代码，而非 try/except/else/finally 的任何子结构。
            # 因此不应以 `_succ not in _region_block_set` 排除，而应检查后继块
            # 是否属于已知结构部分，若不属于则收集为 post-try 块。
            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):
                _try_off_set = set(b.start_offset for b in region.try_blocks)
                _else_off_set = set(b.start_offset for b in region.else_blocks) if region.else_blocks else set()
                _fin_off_set = set(b.start_offset for b in region.finally_blocks)
                _h_off_set = set()
                for _et, _en, _hbs in region.except_handlers:
                    for _hb in _hbs:
                        _h_off_set.add(_hb.start_offset)
                _fc_key_set = set(region.finally_copy_blocks.keys())
                _known_struct = _try_off_set | _else_off_set | _fin_off_set | _h_off_set | _fc_key_set
                for _fc_offset, _fc_keep in region.finally_copy_blocks.items():
                    _fc_block = self.cfg.get_block_by_offset(_fc_offset)
                    if _fc_block is None:
                        continue
                    for _succ in _fc_block.successors:
                        if (_succ.start_offset in _known_struct
                                or _succ in _post_try_seen_r19n2
                                or _succ in _handler_entry_blocks):"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: Old text not found!")
