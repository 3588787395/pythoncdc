#!/usr/bin/env python3
"""Patch debug2 to add trace at top of for loop"""

with open('core/cfg/region_ast_generator_debug2.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = """        for block in sorted(blocks, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue
            if block in _nested_if_skip:"""

new = """        for block in sorted(blocks, key=lambda b: b.start_offset):
            if block.start_offset in (410, 448, 488):
                import sys as _dbg_top
                print(f"TOP @" + str(block.start_offset) + ": gen=" + str(block in self.generated_blocks) + " skip=" + str(block in _nested_if_skip) + " role=" + str(self.region_analyzer.get_block_role(block)), file=_dbg_top.stderr)
            if block in self.generated_blocks:
                continue
            if block in _nested_if_skip:"""

if old in c:
    c = c.replace(old, new, 1)
    with open('core/cfg/region_ast_generator_debug2.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Patched!")
else:
    print("Not found!")