#!/usr/bin/env python3
"""R100: Patch region_ast_generator.py to fix chained compare negate logic"""
import os

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '                            _real_then_offsets = {b.start_offset for b in region.then_blocks}\n                        jumps_to_then = jump_target in _real_then_offsets\n                        negate = jumps_to_then != if_true\n                return _negate_expr(compare_expr) if negate else compare_expr'

new = '''                            # 区域归约算法原则 2（每块唯一归属）+
                            # 原则 4（入口引用语义）：链式比较 IfRegion
                            # 的 then_blocks 可能被外层 LoopRegion 扩展
                            # 吸收了 JUMP_BACKWARD continue 块。排除这些
                            # continue 块避免 negate 误判。
                            _real_then_offsets = set()
                            for b in region.then_blocks:
                                _b_last = b.get_last_instruction()
                                if (_b_last and
                                        _b_last.opname in (
                                            'JUMP_BACKWARD',
                                            'JUMP_BACKWARD_NO_INTERRUPT')
                                        and _b_last.argval is not None):
                                    _jt = self.cfg.get_block_by_offset(
                                        _b_last.argval)
                                    if _jt and _jt.opname == 'FOR_ITER':
                                        continue
                                _real_then_offsets.add(b.start_offset)
                        jumps_to_then = jump_target in _real_then_offsets
                        negate = jumps_to_then != if_true
                return _negate_expr(compare_expr) if negate else compare_expr'''

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('PATCH APPLIED SUCCESSFULLY')
else:
    print('OLD STRING NOT FOUND')
    # Try to find a nearby match
    idx = content.find('_real_then_offsets = {b.start_offset for b in region.then_blocks}')
    if idx >= 0:
        print(f'Found at index {idx}')
        print('Context:', repr(content[idx:idx+200]))
    else:
        print('Variable not found at all')
