import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = """                            _post_try_blocks_r19n2.append(_succ)
            # 标记 post-try 块为 generated，使 IfRegion 跳过它们"""

new_text = """                            _post_try_blocks_r19n2.append(_succ)
            # [R08 fix] Also check finally_copy_blocks successors for post-try blocks.
            # When has_finally=True, CPython creates finally normal-path copies
            # (in finally_copy_blocks) that end with JUMP_FORWARD to post-try code
            # (e.g., `return None` after try-except-else-finally). These post-try
            # blocks are not reachable from else_blocks or try_blocks successors.
            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):
                _region_block_set = set(region.blocks)
                for _fc_offset, _fc_keep in region.finally_copy_blocks.items():
                    _fc_block = self.cfg.get_block_by_offset(_fc_offset)
                    if _fc_block is None:
                        continue
                    for _succ in _fc_block.successors:
                        if (_succ not in _region_block_set
                                and _succ not in _post_try_seen_r19n2
                                and _succ not in _handler_entry_blocks):
                            _has_reraise = any(
                                i.opname == 'RERAISE' for i in _succ.instructions)
                            if _has_reraise:
                                continue
                            if _succ in _all_if_merge_blocks_r19n2:
                                continue
                            _succ_owner_pt = self.region_analyzer.block_to_region.get(_succ)
                            if _succ_owner_pt is not None and _succ_owner_pt is not region:
                                continue
                            _post_try_seen_r19n2.add(_succ)
                            _post_try_blocks_r19n2.append(_succ)
            # 标记 post-try 块为 generated，使 IfRegion 跳过它们"""

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("Old text NOT found!")
