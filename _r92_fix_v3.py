#!/usr/bin/env python3
"""R92 fix v3: Filter blocks with start_offset >= merge_block.start_offset from then_blocks"""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        self._r92_post_if_blocks = []
        if (region.merge_block is not None
                and region.then_blocks
                and region.merge_block in region.then_blocks):
            self._r92_saved_then_blocks = region.then_blocks
            _mb = region.merge_block
            self._r92_post_if_blocks = [b for b in region.then_blocks
                                   if b.start_offset >= _mb.start_offset]
            region.then_blocks = [b for b in region.then_blocks
                                   if b.start_offset < _mb.start_offset]"""

new = """        self._r92_post_if_blocks = []
        if (region.merge_block is not None
                and region.then_blocks
                and any(b.start_offset >= region.merge_block.start_offset
                        for b in region.then_blocks)):
            self._r92_saved_then_blocks = region.then_blocks
            _mb = region.merge_block
            self._r92_post_if_blocks = [b for b in region.then_blocks
                                   if b.start_offset >= _mb.start_offset]
            region.then_blocks = [b for b in region.then_blocks
                                   if b.start_offset < _mb.start_offset]"""

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
