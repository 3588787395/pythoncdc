#!/usr/bin/env python3
"""R93 fix: Generate merge_block as post-if statement in _if_generate_normal
when merge_block is in then_blocks (meaning the region analyzer included
post-if code in then_blocks).

The issue: IfRegion@0 (if include and _query_date > _min_datetime:) has
merge_block=2710 in its blocks but NOT in then_blocks or else_blocks.
The merge_block (2710, which is his_data_dict = get_kline_by_count_new(...))
and block 2758 (return his_data_dict) should be generated as post-if
statements, but they're only generated when _should_emit is True (R15-N5
condition for LoopRegion).

Fix: Also generate merge_block as post-if when:
1. merge_block is not in then_blocks or else_blocks
2. merge_block is not already generated
3. merge_block has meaningful instructions (not just JUMP/NOP)
"""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the post-if generation block in _if_generate_normal
# We need to add an additional condition to _should_emit
old = """            _should_emit = False
            if not _mb_in_nested_structural:
                # 检查 R15-N5 触发条件：merge_block 是嵌套 LoopRegion 的 for_iter_exit
                # 同时检查 then_blocks 和 else_blocks
                _then_block_set = set(region.then_blocks)
                _else_block_set = set(region.else_blocks or [])
                for _lr in self.region_analyzer.regions:
                    if not isinstance(_lr, LoopRegion):
                        continue
                    if _lr is region:
                        continue
                    if region.merge_block not in _lr.else_blocks:
                        continue
                    if _lr.entry is not None and (_lr.entry in _then_block_set
                                                   or _lr.entry in _else_block_set):
                        _should_emit = True
                        break"""

new = """            _should_emit = False
            if not _mb_in_nested_structural:
                # 检查 R15-N5 触发条件：merge_block 是嵌套 LoopRegion 的 for_iter_exit
                # 同时检查 then_blocks 和 else_blocks
                _then_block_set = set(region.then_blocks)
                _else_block_set = set(region.else_blocks or [])
                for _lr in self.region_analyzer.regions:
                    if not isinstance(_lr, LoopRegion):
                        continue
                    if _lr is region:
                        continue
                    if region.merge_block not in _lr.else_blocks:
                        continue
                    if _lr.entry is not None and (_lr.entry in _then_block_set
                                                   or _lr.entry in _else_block_set):
                        _should_emit = True
                        break
                # R93: Also emit merge_block as post-if when it contains
                # meaningful instructions (not just JUMP/NOP) and is not
                # already generated. The region analyzer may include the
                # merge_block (first block AFTER the if-else) in the
                # IfRegion's blocks without assigning it to then/else.
                # Without this, merge_block's statements (e.g.
                # his_data_dict = get_kline_by_count_new(...)) are never
                # emitted, and the Python compiler generates spurious
                # implicit return None at the end of the then branch.
                if not _should_emit and region.merge_block not in self.generated_blocks:
                    _mb_meaningful = [i for i in region.merge_block.instructions
                                      if i.opname not in ('RESUME', 'NOP', 'CACHE',
                                                          'JUMP_FORWARD', 'JUMP_BACKWARD',
                                                          'JUMP_ABSOLUTE')]
                    if _mb_meaningful:
                        _should_emit = True"""

count = content.count(old)
print(f'Found {count} occurrences')
if count == 1:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Applied successfully')
elif count == 0:
    print('Not found')
else:
    print(f'ERROR: {count} occurrences')
