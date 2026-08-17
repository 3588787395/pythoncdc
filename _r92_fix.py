#!/usr/bin/env python3
"""R92 fix: Filter merge_block and subsequent blocks from then_blocks.
Also generate merge_block as post-if statement in _if_generate_normal."""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: In _if_generate_then_branch, filter merge_block from then_blocks
old1 = "        then_stmts = self._process_if_blocks(region.then_blocks, region, branch='then')"
new1 = """        # R92: Filter out merge_block and subsequent blocks from then_blocks.
        # Similar to R91 fix for elif_bodies: the region analyzer may include
        # the merge_block (first block AFTER the if) in then_blocks, causing
        # all post-if code to be generated inside the then body and generating
        # spurious implicit return None (LOAD_CONST None + RETURN_VALUE instead
        # of JUMP_FORWARD to merge_block).
        _r92_saved_then_blocks = None
        _r92_post_if_blocks = []
        if (region.merge_block is not None
                and region.then_blocks
                and region.merge_block in region.then_blocks):
            _r92_saved_then_blocks = region.then_blocks
            _mb = region.merge_block
            _r92_post_if_blocks = [b for b in region.then_blocks
                                   if b.start_offset >= _mb.start_offset]
            region.then_blocks = [b for b in region.then_blocks
                                   if b.start_offset < _mb.start_offset]
        then_stmts = self._process_if_blocks(region.then_blocks, region, branch='then')
        # R92: Restore original then_blocks
        if _r92_saved_then_blocks is not None:
            region.then_blocks = _r92_saved_then_blocks"""

count1 = content.count(old1)
print(f'Fix 1: Found {count1} occurrences')
if count1 == 1:
    content = content.replace(old1, new1, 1)
    
    # Fix 2: In _if_generate_normal, generate post-if blocks after the if
    old2 = """        if _5_post_extra:
            if isinstance(if_result, list):
                if_result = if_result + _5_post_extra
            else:
                if_result = [if_result] + _5_post_extra
        return if_result"""
    
    new2 = """        if _5_post_extra:
            if isinstance(if_result, list):
                if_result = if_result + _5_post_extra
            else:
                if_result = [if_result] + _5_post_extra
        # R92: Generate post-if blocks (merge_block and subsequent blocks that
        # were filtered out from then_blocks) as top-level statements after
        # the if structure.
        if _r92_post_if_blocks:
            for _b in _r92_post_if_blocks:
                self.generated_blocks.discard(_b)
                self.generated_offsets.discard(_b.start_offset)
            _r92_post_stmts = self._process_if_blocks(
                _r92_post_if_blocks, region, branch='then')
            for _b in _r92_post_if_blocks:
                self.generated_blocks.add(_b)
                self.generated_offsets.add(_b.start_offset)
            if _r92_post_stmts:
                if isinstance(if_result, list):
                    if_result = if_result + _r92_post_stmts
                else:
                    if_result = [if_result] + _r92_post_stmts
        return if_result"""
    
    count2 = content.count(old2)
    print(f'Fix 2: Found {count2} occurrences')
    if count2 == 1:
        content = content.replace(old2, new2, 1)
        with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Applied successfully')
    elif count2 == 0:
        print('ERROR: Fix 2 pattern not found')
    else:
        print(f'ERROR: {count2} occurrences of fix 2')
elif count1 == 0:
    print('Fix 1 not found or already applied')
else:
    print(f'ERROR: {count1} occurrences of fix 1')
