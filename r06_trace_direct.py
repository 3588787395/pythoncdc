#!/usr/bin/env python3
"""Direct trace: Insert debug prints into _process_if_blocks"""

import sys, types
sys.path.insert(0, '.')

# First, read the source and patch it
with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    source = f.read()

# Find the for loop and insert debug print after "if block in self.generated_blocks: continue"
# and after "if block in _nested_if_skip: continue"
# and at the _nested_if_entry_generate check

# Insert debug print right after the for loop line
old = "        for block in sorted(blocks, key=lambda b: b.start_offset):\n            if block in self.generated_blocks:"
new = """        for block in sorted(blocks, key=lambda b: b.start_offset):
            if block.start_offset in (410, 448, 488):
                import sys as _dbg_sys
                print(f"TRACE block@{block.start_offset}: gen={block in self.generated_blocks} skip={block in _nested_if_skip} entry_gen={block in _nested_if_entry_generate} entry_skip={block in _nested_if_entry_skip}", file=_dbg_sys.stderr)
            if block in self.generated_blocks:"""

if old in source:
    source = source.replace(old, new, 1)
    # Write patched version
    with open('core/cfg/region_ast_generator_debug.py', 'w', encoding='utf-8') as f:
        f.write(source)
    print("Debug patch applied")
else:
    print("Target not found!")
    # Show the actual lines
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'for block in sorted(blocks' in line:
            for j in range(i, min(len(lines), i+5)):
                print(f"  {j+1}: {lines[j]}")
            break