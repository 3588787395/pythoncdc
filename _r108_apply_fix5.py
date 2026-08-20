"""Fix reversed condition in finally_copy_blocks post-try detection"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                    for _succ in _fc_block.successors:
                        import sys as _sys_dbg_fs
                        _fs_in_known = _succ.start_offset in _known_struct
                        _fs_in_seen = _succ in _post_try_seen_r19n2
                        _fs_in_he = _succ in _handler_entry_blocks
                        print(f"DEBUG fc succ: fc={_fc_offset}, succ={_succ.start_offset}, in_known={_fs_in_known}, in_seen={_fs_in_seen}, in_he={_fs_in_he}", file=_sys_dbg_fs.stderr)
                        if (_succ.start_offset in _known_struct
                                or _succ in _post_try_seen_r19n2
                                or _succ in _handler_entry_blocks):
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
                            _post_try_blocks_r19n2.append(_succ)"""

new = """                    for _succ in _fc_block.successors:
                        if (_succ.start_offset not in _known_struct
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
                            _post_try_blocks_r19n2.append(_succ)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: Old text not found!")
