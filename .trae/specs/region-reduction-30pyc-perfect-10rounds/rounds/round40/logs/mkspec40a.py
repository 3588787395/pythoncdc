# -*- coding: utf-8 -*-
"""Round 40 line A: emit spec40a.json (candidate R40-A) for the mirror harness.

R40-A  merge-into-else promotion for an escaping then arm:  the gate at
core/cfg/region_ast_generator.py:17099-17116 (inside _if_generate_normal) promotes
IfRegion.merge_block into region.else_blocks *only* when the merge block is pure
(no meaningful instructions).  When the then arm escapes straight back to the loop
header, merge_block is not a merge at all -- it is the else arm -- and purity is the
wrong test.

Adopted from D:/Temp/r39diagB/ANALYSIS.md section 4 after re-verifying, against the
LANDED bytes (sha cc1254fa30410f2b9954): (a) the anchor is still unique, (b) the gate
still sits at 17099-17117, (c) the 4 owned rows are still partial in pyc_index.json.
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
    '                        # [R40-A] 区域归约算法原则 1（每块 = 前导语句 + 唯一终止符）+ 原则 2\n'
    '                        # （每块唯一归属）：merge_block 只有真的汇合两臂时才是 merge。\n'
    '                        # 判据全部为结构事实：真臂尾块（then_blocks 中没有在 then_blocks 内\n'
    '                        # 的后继者）的终结边是无条件跳转，且目标恰为包围本 if 的循环头\n'
    '                        # （不是 merge_block）——此时两臂互斥、各自回到循环头，merge_block\n'
    '                        # 不是汇合点而是假臂本体，必须认给 else_blocks 并撤销 merge 角色。\n'
    '                        # 留在原处发射时它由父循环按自然回边次序发射，AST 上 if 的 orelse\n'
    '                        # 为 None，真臂尾的 JUMP_BACKWARD 与假臂尾的 JUMP_BACKWARD 在重编译\n'
    '                        # 时塌缩成同一条（实测少发一条），假臂在 AST 上成为无终止符的摊平分支。\n'
    '                        # 与既有纯度判据互斥并联：纯 merge 分支逐字保留，不改变其世界。\n'
    '                        _mb_then_escapes = False\n'
    '                        _mb_tset = set(region.then_blocks or [])\n'
    '                        for _mb_ttb in _mb_tset:\n'
    '                            if any(_mb_s in _mb_tset for _mb_s in (_mb_ttb.successors or ())):\n'
    '                                continue\n'
    '                            _mb_ttl = _mb_ttb.get_last_instruction()\n'
    '                            if (_mb_ttl is not None\n'
    '                                    and _mb_ttl.opname in (\'JUMP_BACKWARD\',\n'
    '                                                          \'JUMP_BACKWARD_NO_INTERRUPT\',\n'
    '                                                          \'JUMP_FORWARD\', \'JUMP_ABSOLUTE\')\n'
    '                                    and isinstance(_mb_ttl.argval, int)\n'
    '                                    and self.cfg.get_block_by_offset(_mb_ttl.argval) is _loop_hdr):\n'
    '                                _mb_then_escapes = True\n'
    '                                break\n'
    '                        if not _mb_meaningful or _mb_then_escapes:\n'
    '                            region.else_blocks = [region.merge_block]\n'
    '                            region.merge_block = None\n'
)

assert ANCHOR.count('\n') == 8, ANCHOR.count('\n')
assert REPL.endswith('                            region.merge_block = None\n')
print('inserted line delta', REPL.count('\n') - ANCHOR.count('\n'))
spec = {'file': 'core/cfg/region_ast_generator.py', 'anchor': ANCHOR, 'repl': REPL}
out = os.path.join(HERE, 'spec40a.json')
io.open(out, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote', out, 'repl lines', REPL.count('\n'))
