#!/usr/bin/env python3
"""Round 06: Apply fix for post-store conditional jump handling in _generate_boolop."""
import re

FILE = 'core/cfg/region_ast_generator.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                        if _first_store_idx >= 0:
                            _post_store_clean = []
                            for _pi in _merge_instrs[_first_store_idx + 1:]:
                                if _pi.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                                                  'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT'):
                                    break
                                _post_store_clean.append(_pi)
                            if _post_store_clean:
                                _stmts = self._generate_stmts_from_instrs(
                                    _post_store_clean, region.merge_block)
                                for s in _stmts:
                                    results.append(s)"""

new = """                        if _first_store_idx >= 0:
                            _post_store_clean = []
                            _cond_jump_r89 = None
                            for _pi in _merge_instrs[_first_store_idx + 1:]:
                                if _pi.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                                                  'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT'):
                                    break
                                if _pi.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                    _cond_jump_r89 = _pi
                                    break
                                _post_store_clean.append(_pi)
                            # [R89] Region reduction principle 2 (unique ownership):
                            # merge_block post-store instructions may contain an if
                            # condition (e.g. `if 'name' in my_dict: value = ...`).
                            # The conditional jump and its preceding expression must
                            # be separated from regular statements and generated as
                            # an If statement, not an Expr statement.
                            if _cond_jump_r89:
                                _cond_expr_instrs_r89 = []
                                _stmt_instrs_r89 = list(_post_store_clean)
                                while _stmt_instrs_r89:
                                    _last_r89 = _stmt_instrs_r89[-1]
                                    if _last_r89.opname in ('STORE_FAST', 'STORE_NAME',
                                            'STORE_GLOBAL', 'STORE_DEREF', 'STORE_ATTR',
                                            'STORE_SUBSCR', 'POP_TOP'):
                                        break
                                    _cond_expr_instrs_r89.insert(0, _stmt_instrs_r89.pop())
                                if _cond_expr_instrs_r89:
                                    _cond_expr_r89 = self.expr_reconstructor.reconstruct(
                                        _cond_expr_instrs_r89)
                                    if _cond_expr_r89 is not None:
                                        if _stmt_instrs_r89:
                                            _stmts = self._generate_stmts_from_instrs(
                                                _stmt_instrs_r89, region.merge_block)
                                            for s in _stmts:
                                                results.append(s)
                                        _jump_tgt_r89 = _cond_jump_r89.argval
                                        _fall_through_r89 = _cond_jump_r89.offset + 2
                                        _then_blk_r89 = None
                                        _else_blk_r89 = None
                                        if 'FALSE' in _cond_jump_r89.opname:
                                            _else_blk_r89 = self.cfg.get_block_by_offset(_jump_tgt_r89)
                                            _then_blk_r89 = self.cfg.get_block_by_offset(_fall_through_r89)
                                        elif 'TRUE' in _cond_jump_r89.opname:
                                            _then_blk_r89 = self.cfg.get_block_by_offset(_jump_tgt_r89)
                                            _else_blk_r89 = self.cfg.get_block_by_offset(_fall_through_r89)
                                        else:
                                            _then_blk_r89 = self.cfg.get_block_by_offset(_fall_through_r89)
                                            _else_blk_r89 = self.cfg.get_block_by_offset(_jump_tgt_r89)
                                        _then_body_r89 = []
                                        if _then_blk_r89:
                                            self.generated_blocks.add(_then_blk_r89)
                                            self.generated_offsets.add(_then_blk_r89.start_offset)
                                            _then_body_r89 = self._generate_block_statements(_then_blk_r89)
                                        _if_negate_r89 = ('TRUE' in _cond_jump_r89.opname
                                                          or 'NONE' in _cond_jump_r89.opname)
                                        _test_r89 = _cond_expr_r89
                                        if _if_negate_r89:
                                            _test_r89 = _negate_expr(_cond_expr_r89)
                                        if not _then_body_r89:
                                            _then_body_r89 = [{'type': 'Pass'}]
                                        results.append({
                                            'type': 'If',
                                            'test': _test_r89,
                                            'body': _then_body_r89,
                                            'orelse': [],
                                        })
                                    else:
                                        if _post_store_clean:
                                            _stmts = self._generate_stmts_from_instrs(
                                                _post_store_clean, region.merge_block)
                                            for s in _stmts:
                                                results.append(s)
                                else:
                                    if _post_store_clean:
                                        _stmts = self._generate_stmts_from_instrs(
                                            _post_store_clean, region.merge_block)
                                        for s in _stmts:
                                            results.append(s)
                            elif _post_store_clean:
                                _stmts = self._generate_stmts_from_instrs(
                                    _post_store_clean, region.merge_block)
                                for s in _stmts:
                                    results.append(s)"""

if old not in content:
    print("ERROR: old string not found!")
    # Try to find a partial match
    for i in range(0, len(content) - 100, 50):
        if content[i:i+50] == old[:50]:
            print(f"  Partial match at offset {i}: ...{content[i:i+100]}...")
            break
else:
    content = content.replace(old, new, 1)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK: fix applied successfully")
