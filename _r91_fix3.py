#!/usr/bin/env python3
"""R91 fix v3: Only filter when merge_block is directly in elif_bodies[0].
Use BFS from merge_block to find all blocks reachable from merge_block
that are NOT reachable from other elif body blocks (before merge_block)."""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        then_stmts = self._if_generate_then_branch(region)
        elif_part = self._if_generate_elif_chain(region)"""

new = """        then_stmts = self._if_generate_then_branch(region)
        # R91: When the region analyzer incorrectly includes the merge_block
        # (first block AFTER the if-elif-else) and its reachable successors
        # in elif_bodies[0], all post-if code gets nested inside the elif body.
        # This generates spurious implicit return None and changes code scope.
        # Fix: detect merge_block in elif_bodies[0], split blocks into
        # pre-merge (elif body) and post-merge (post-if statements).
        _r91_saved_elif_bodies_0 = None
        _r91_post_if_blocks = []
        if (region.merge_block is not None
                and getattr(region, 'elif_bodies', None)
                and region.elif_bodies
                and region.merge_block in region.elif_bodies[0]
                and any(b.start_offset < region.merge_block.start_offset
                        for b in region.elif_bodies[0])):
            _r91_saved_elif_bodies_0 = region.elif_bodies[0]
            _mb = region.merge_block
            _pre_merge = [b for b in region.elif_bodies[0]
                          if b.start_offset < _mb.start_offset]
            _post_merge = [b for b in region.elif_bodies[0]
                           if b.start_offset >= _mb.start_offset]
            # Only move post-merge blocks that are NOT reachable from pre-merge
            # blocks (i.e., blocks that are only reachable from merge_block).
            # Blocks reachable from pre-merge blocks may be legitimate elif
            # body blocks (e.g., backward jump targets).
            _pre_merge_set = set(_pre_merge)
            _reachable_from_pre = set()
            _worklist = list(_pre_merge)
            while _worklist:
                _b = _worklist.pop()
                for _s in _b.successors:
                    if _s not in _reachable_from_pre and _s in set(region.elif_bodies[0]):
                        _reachable_from_pre.add(_s)
                        _worklist.append(_s)
            _r91_post_if_blocks = [b for b in _post_merge
                                   if b not in _reachable_from_pre]
            region.elif_bodies[0] = [b for b in region.elif_bodies[0]
                                     if b not in _r91_post_if_blocks]
        elif_part = self._if_generate_elif_chain(region)
        # R91: Restore original elif_bodies[0] if modified
        if _r91_saved_elif_bodies_0 is not None:
            region.elif_bodies[0] = _r91_saved_elif_bodies_0"""

count = content.count(old)
print(f'Found {count} occurrences')
if count == 1:
    content = content.replace(old, new, 1)
    
    # Add post-if generation before "return result"
    old2 = """        return result

    def _build_chained_compare_from_region_data(self, region: IfRegion) -> Optional[Dict[str, Any]]:"""
    
    new2 = """        # R91: Generate post-if blocks (merge_block and subsequent blocks
        # that were incorrectly included in elif_bodies[0]) as top-level
        # statements after the if-elif-else structure.
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
