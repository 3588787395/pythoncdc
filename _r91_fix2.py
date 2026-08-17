#!/usr/bin/env python3
"""R91 fix: Filter merge_block and subsequent blocks from elif_bodies[0]
before calling _if_generate_elif_chain. Generate them as post-if statements."""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        then_stmts = self._if_generate_then_branch(region)
        elif_part = self._if_generate_elif_chain(region)"""

new = """        then_stmts = self._if_generate_then_branch(region)
        # R91: Filter out merge_block and subsequent blocks from elif_bodies[0].
        # The region analyzer may include the merge_block (first block AFTER the
        # if-elif-else) and all reachable blocks in elif_bodies[0]. This causes
        # all post-if code to be generated inside the elif body, changing code
        # scope and generating spurious implicit return None.
        # Fix: temporarily strip blocks at/after merge_block from elif_bodies[0],
        # generate them as post-if statements after the if-elif-else structure.
        _r91_saved_elif_bodies_0 = None
        _r91_post_if_blocks = []
        if (region.merge_block is not None
                and getattr(region, 'elif_bodies', None)
                and region.elif_bodies
                and any(b.start_offset >= region.merge_block.start_offset
                        for b in region.elif_bodies[0])):
            _r91_saved_elif_bodies_0 = region.elif_bodies[0]
            _mb_off = region.merge_block.start_offset
            _r91_post_if_blocks = [b for b in region.elif_bodies[0]
                                   if b.start_offset >= _mb_off]
            region.elif_bodies[0] = [b for b in region.elif_bodies[0]
                                     if b.start_offset < _mb_off]
        elif_part = self._if_generate_elif_chain(region)
        # R91: Restore original elif_bodies[0] if modified
        if _r91_saved_elif_bodies_0 is not None:
            region.elif_bodies[0] = _r91_saved_elif_bodies_0"""

count = content.count(old)
print(f'Found {count} occurrences')
if count == 1:
    content = content.replace(old, new, 1)
    
    # Now add the post-if generation before "return result" at the end of
    # _if_generate_full_elif_chain. Find the return statement.
    old2 = """        return result

    def _build_chained_compare_from_region_data(self, region: IfRegion) -> Optional[Dict[str, Any]]:"""
    
    new2 = """        # R91: Generate post-if blocks (merge_block and subsequent blocks that
        # were filtered out from elif_bodies[0]) as top-level statements after
        # the if-elif-else structure. This ensures code after the if-elif-else
        # is at the correct scope (function body level, not inside elif body).
        if _r91_post_if_blocks:
            for _b in _r91_post_if_blocks:
                self.generated_blocks.discard(_b)
                self.generated_offsets.discard(_b.start_offset)
            _r91_post_stmts = self._process_if_blocks(
                _r91_post_if_blocks, region, branch='then')
            for _b in _r91_post_if_blocks:
                self.generated_blocks.add(_b)
                self.generated_offsets.add(_b.start_offset)
            if _r91_post_stmts:
                if isinstance(result, list):
                    result = result + _r91_post_stmts
                else:
                    result = [result] + _r91_post_stmts
        return result

    def _build_chained_compare_from_region_data(self, region: IfRegion) -> Optional[Dict[str, Any]]:"""
    
    count2 = content.count(old2)
    print(f'Found {count2} occurrences of return pattern')
    if count2 == 1:
        content = content.replace(old2, new2, 1)
        with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Applied successfully')
    elif count2 == 0:
        print('ERROR: return pattern not found')
    else:
        print(f'ERROR: {count2} occurrences of return pattern')
elif count == 0:
    print('Not found or already applied')
else:
    print(f'ERROR: {count} occurrences')
