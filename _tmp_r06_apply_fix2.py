#!/usr/bin/env python3
"""Round 06: Fix - don't mark then-block as generated before calling _generate_block_statements."""

FILE = 'core/cfg/region_ast_generator.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                                        _then_body_r89 = []
                                        if _then_blk_r89:
                                            self.generated_blocks.add(_then_blk_r89)
                                            self.generated_offsets.add(_then_blk_r89.start_offset)
                                            _then_body_r89 = self._generate_block_statements(_then_blk_r89)"""

new = """                                        _then_body_r89 = []
                                        if _then_blk_r89:
                                            _then_body_r89 = self._generate_block_statements(_then_blk_r89)
                                            self.generated_blocks.add(_then_blk_r89)
                                            self.generated_offsets.add(_then_blk_r89.start_offset)"""

if old not in content:
    print("ERROR: old string not found!")
else:
    content = content.replace(old, new, 1)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK: fix applied successfully")
