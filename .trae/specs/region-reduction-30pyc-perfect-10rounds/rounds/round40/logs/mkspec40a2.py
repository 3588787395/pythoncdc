# -*- coding: utf-8 -*-
"""Round 40 line A, candidate 2 (R40-A2 = tightened R40-A).

diagB's predicate fired when *some* then-arm tail escaped to the loop header.  That is
not enough to prove "merge_block is not a merge": with two tails, the other one may
still fall through into merge_block, in which case merge_block really is the join.
R40-A2 states the provable form -- every then-arm tail escapes to the loop header AND
no then-arm block has merge_block as a successor.  All terms stay structural (block
identity, successor relation, terminator opcode class, region roles).
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')

ANCHOR = (
    '                    if _mb_target is not None and _mb_target in (_loop_hdr, _loop_cond):\n'
    '                        _mb_meaningful = [i for i in region.merge_block.instructions\n'
    '                                          if i.opname not in (\'RESUME\', \'NOP\', \'CACHE\', \'PUSH_NULL\', \'POP_TOP\')\n'
    '                                          and i.opname not in (\'JUMP_BACKWARD\', \'JUMP_BACKWARD_NO_INTERRUPT\',\n'
    '                                                               \'JUMP_FORWARD\', \'JUMP_ABSOLUTE\')]\n'
    '                        if not _mb_meaningful:\n'
    '                            region.else_blocks = [region.merge_block]\n'
    '                            region.merge_block = None\n'
)

REPL = (
    '                    if _mb_target is not None and _mb_target in (_loop_hdr, _loop_cond):\n'
    '                        _mb_meaningful = [i for i in region.merge_block.instructions\n'
    '                                          if i.opname not in (\'RESUME\', \'NOP\', \'CACHE\', \'PUSH_NULL\', \'POP_TOP\')\n'
    '                                          and i.opname not in (\'JUMP_BACKWARD\', \'JUMP_BACKWARD_NO_INTERRUPT\',\n'
    '                                                               \'JUMP_FORWARD\', \'JUMP_ABSOLUTE\')]\n'
    '                        # [R40-A2] 区域归约算法原则 1（每块 = 前导语句 + 唯一终止符）+ 原则 2\n'
    '                        # （每块唯一归属）：merge_block 只有真的汇合两臂时才是 merge。\n'
    '                        # 判据全部为结构事实：① then 臂的任何块都不以 merge_block 为后继；\n'
    '                        # ② then 臂的每条尾块（在 then_blocks 内无后继者）的终结边都是无条件\n'
    '                        # 跳转且目标恰为包围本 if 的循环头。①+② 一起才证明两臂互斥、各自\n'
    '                        # 回到循环头，merge_block 不是汇合点而是假臂本体：留在原处由父循环\n'
    '                        # 按自然回边次序发射时，AST 上 if 的 orelse 为 None，真臂尾的\n'
    '                        # JUMP_BACKWARD 与假臂尾的 JUMP_BACKWARD 在重编译时塌缩成同一条\n'
    '                        # （实测少发一条），假臂在 AST 上成为无终止符的摊平分支。\n'
    '                        # 归约方式：认给 else_blocks 并撤销 merge 角色，由 else 臂生成器发射。\n'
    '                        # 与既有纯度判据互斥并联：纯 merge 分支逐字保留，不改变其世界。\n'
    '                        _mb_then_escapes = False\n'
    '                        _mb_tset = set(region.then_blocks or [])\n'
    '                        if _mb_tset:\n'
    '                            _mb_reaches = any(\n'
    '                                region.merge_block in set(_mb_b.successors or ())\n'
    '                                for _mb_b in _mb_tset)\n'
    '                            _mb_tails = [_mb_b for _mb_b in _mb_tset\n'
    '                                         if not (set(_mb_b.successors or ()) & _mb_tset)]\n'
    '                            _mb_all_escape = bool(_mb_tails)\n'
    '                            for _mb_ttb in _mb_tails:\n'
    '                                _mb_ttl = _mb_ttb.get_last_instruction()\n'
    '                                if not (_mb_ttl is not None\n'
    '                                        and _mb_ttl.opname in (\'JUMP_BACKWARD\',\n'
    '                                                              \'JUMP_BACKWARD_NO_INTERRUPT\',\n'
    '                                                              \'JUMP_FORWARD\', \'JUMP_ABSOLUTE\')\n'
    '                                        and isinstance(_mb_ttl.argval, int)\n'
    '                                        and self.cfg.get_block_by_offset(\n'
    '                                            _mb_ttl.argval) is _loop_hdr):\n'
    '                                    _mb_all_escape = False\n'
    '                                    break\n'
    '                            _mb_then_escapes = _mb_all_escape and not _mb_reaches\n'
    '                        if not _mb_meaningful or _mb_then_escapes:\n'
    '                            region.else_blocks = [region.merge_block]\n'
    '                            region.merge_block = None\n'
)

assert ANCHOR.count('\n') == 8, ANCHOR.count('\n')
assert REPL.endswith('                            region.merge_block = None\n')
print('inserted line delta', REPL.count('\n') - ANCHOR.count('\n'))
spec = {'file': 'core/cfg/region_ast_generator.py', 'anchor': ANCHOR, 'repl': REPL}
out = os.path.join(HERE, 'spec40a2.json')
io.open(out, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote', out, 'repl lines', REPL.count('\n'))
